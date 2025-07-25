"""GCP deployment implementation using CDKTF."""

import hashlib
import subprocess
from pathlib import Path

from cdktf import TerraformOutput, TerraformStack
from cdktf_cdktf_provider_google.artifact_registry_repository import (
    ArtifactRegistryRepository,
    ArtifactRegistryRepositoryCleanupPolicies,
    ArtifactRegistryRepositoryCleanupPoliciesCondition,
    ArtifactRegistryRepositoryCleanupPoliciesMostRecentVersions,
)
from cdktf_cdktf_provider_google.cloud_run_v2_service import (
    CloudRunV2Service,
    CloudRunV2ServiceTemplate,
    CloudRunV2ServiceTemplateContainers,
    CloudRunV2ServiceTemplateContainersPorts,
)
from cdktf_cdktf_provider_google.cloud_run_v2_service_iam_member import (
    CloudRunV2ServiceIamMember,
)
from cdktf_cdktf_provider_google.project_iam_member import ProjectIamMember
from cdktf_cdktf_provider_google.provider import GoogleProvider
from cdktf_cdktf_provider_google.service_account import ServiceAccount
from cdktf_cdktf_provider_null.provider import NullProvider
from cdktf_cdktf_provider_null.resource import Resource as NullResource
from constructs import Construct


class EmsipiGcpStack(TerraformStack):
    """CDKTF stack for emsipi GCP deployment."""

    def __init__(  # noqa: PLR0913
        self,
        scope: Construct,
        construct_id: str,
        project_id: str,
        region: str = "us-central1",
        artifact_repository_id: str = "emsipi-repo",
        service_name: str = "emsipi",
        working_dir: str | None = None,
    ) -> None:
        """Initialize the GCP stack.

        Args:
            scope: The construct scope
            construct_id: The construct ID
            project_id: GCP project ID
            region: GCP region
            artifact_repository_id: Artifact repository ID
            service_name: Service name
            working_dir: Working directory for the stack
        """
        super().__init__(scope, construct_id)

        # Configuration
        self.project_id: str = project_id
        self.region: str = region
        self.artifact_repository_id: str = artifact_repository_id
        self.service_name: str = service_name
        self.working_dir: str | None = working_dir

        # Type annotations for class attributes
        self.artifact_repo: ArtifactRegistryRepository
        self.run_sa: ServiceAccount
        self.build_resource: NullResource
        self.cloud_run_service: CloudRunV2Service
        self.full_image: str

        # Providers
        _ = GoogleProvider(
            self,
            "google",
            project=self.project_id,
            region=self.region,
        )

        _ = NullProvider(self, "null")

        # Resources
        self._create_artifact_registry()
        self._create_service_account()
        self._create_build_and_push()
        self._create_cloud_run_service()
        self._create_public_access()

    def _create_artifact_registry(self) -> None:
        """Create Artifact Registry repository with cleanup policies."""
        self.artifact_repo = ArtifactRegistryRepository(
            self,
            "repo",
            location=self.region,
            repository_id=self.artifact_repository_id,
            format="DOCKER",
            description=f"Docker repo for {self.service_name}",
            cleanup_policy_dry_run=False,
            cleanup_policies=[
                ArtifactRegistryRepositoryCleanupPolicies(
                    id="delete-older-than-30d",
                    action="DELETE",
                    condition=ArtifactRegistryRepositoryCleanupPoliciesCondition(
                        older_than="2592000s",  # 30 days
                        tag_state="ANY",
                    ),
                ),
                ArtifactRegistryRepositoryCleanupPolicies(
                    id="keep-last-3",
                    action="KEEP",
                    most_recent_versions=ArtifactRegistryRepositoryCleanupPoliciesMostRecentVersions(
                        keep_count=3
                    ),
                ),
            ],
            lifecycle={"prevent_destroy": True},
        )

    def _create_service_account(self) -> None:
        """Create service account for Cloud Run."""
        self.run_sa = ServiceAccount(
            self,
            "run_sa",
            account_id=f"{self.service_name}-sa",
            display_name=f"SA for Cloud Run service {self.service_name}",
        )

        # Grant Artifact Registry reader role
        _ = ProjectIamMember(
            self,
            "run_sa_artifact_reader",
            project=self.project_id,
            role="roles/artifactregistry.reader",
            member=f"serviceAccount:{self.run_sa.email}",
        )

    def _get_image_info(self) -> tuple[str, str]:
        """Get image name and tag based on git repository state.

        Returns:
            Tuple of (full_image_name, tag)
        """
        # Get git index hash (similar to Terraform's filesha256)
        git_index_path = (
            Path(__file__).parent.parent.parent.parent / ".git" / "index"
        )
        if git_index_path.exists():
            with git_index_path.open("rb") as f:
                repo_hash = hashlib.sha256(f.read()).hexdigest()
            tag = repo_hash[:12]  # First 12 chars like short SHA
        else:
            tag = "latest"

        image_name = (
            f"{self.region}-docker.pkg.dev/{self.project_id}/"
            f"{self.artifact_repository_id}/{self.service_name}"
        )
        full_image = f"{image_name}:{tag}"

        return full_image, tag

    def _create_build_and_push(self) -> None:
        """Create Cloud Build trigger for building and pushing container."""
        full_image, tag = self._get_image_info()
        self.full_image = full_image

        # Get Dockerfile hash for triggering rebuilds
        dockerfile_path = (
            Path(__file__).parent.parent.parent.parent / "Dockerfile"
        )
        dockerfile_hash = ""
        if dockerfile_path.exists():
            with dockerfile_path.open("rb") as f:
                dockerfile_hash = hashlib.sha256(f.read()).hexdigest()

        git_index = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )
        git_index_hash = (
            git_index.stdout.strip() if git_index.returncode == 0 else ""
        )

        self.build_resource = NullResource(
            self,
            "build_and_push",
            triggers={
                "dockerfile_hash": dockerfile_hash,
                "tag": tag,
                "git_index_hash": git_index_hash,
            },
            provisioners=[
                {
                    "type": "local-exec",
                    "command": f"""
                        gcloud builds submit {self.working_dir} \\
                          --project {self.project_id} \\
                          --region {self.region} \\
                          --tag {full_image}
                    """,
                }
            ],
            depends_on=[self.artifact_repo],
        )

    def _create_cloud_run_service(self) -> None:
        """Create Cloud Run v2 service."""
        self.cloud_run_service = CloudRunV2Service(
            self,
            "service",
            name=self.service_name,
            location=self.region,
            ingress="INGRESS_TRAFFIC_ALL",
            template=CloudRunV2ServiceTemplate(
                containers=[
                    CloudRunV2ServiceTemplateContainers(
                        image=self.full_image,
                        ports=CloudRunV2ServiceTemplateContainersPorts(
                            container_port=8080
                        ),
                    )
                ],
                service_account=self.run_sa.email,
            ),
            depends_on=[self.build_resource],
            deletion_protection=False,
        )

    def _create_public_access(self) -> None:
        """Make the Cloud Run service publicly accessible."""
        _ = CloudRunV2ServiceIamMember(
            self,
            "public_invoker",
            name=self.cloud_run_service.name,
            location=self.cloud_run_service.location,
            role="roles/run.invoker",
            member="allUsers",
        )

        # Output the service URL
        _ = TerraformOutput(
            self,
            "service_url",
            value=self.cloud_run_service.uri,
            description="URL of the deployed Cloud Run service",
        )
