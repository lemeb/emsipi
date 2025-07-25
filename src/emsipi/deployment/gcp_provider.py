"""GCP deployment provider implementation."""

import logging
from typing import TYPE_CHECKING, Any, override

from cdktf import App

from emsipi.config.config import EmsipiConfig, GoogleProviderConfig

from .base import DeploymentProvider
from .gcp import EmsipiGcpStack

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class GCPProvider(DeploymentProvider[GoogleProviderConfig]):
    """GCP deployment provider."""

    def __init__(
        self,
        general_config: EmsipiConfig,
        provider_config: GoogleProviderConfig,
    ) -> None:
        """Initialize GCP provider.

        Args:
            general_config: Emsipi configuration
            provider_config: GCP configuration
        """
        self.stack_name: str = f"{general_config.server_name}-google"
        self.server_name: str = general_config.clean_server_name
        self.project_id: str = provider_config.project
        self.region: str = provider_config.region
        self.service_name: str = provider_config.service_name
        self.artifact_repository_id: str = provider_config.artifact_registry
        self.working_dir: Path = general_config.working_directory

    @override
    def synth(self) -> None:
        """Synthesize the application."""
        app = App(outdir=str(self.working_dir / "cdktf.out"))
        _ = EmsipiGcpStack(
            app,
            self.stack_name,
            project_id=self.project_id,
            region=self.region,
            artifact_repository_id=self.artifact_repository_id,
            service_name=self.service_name,
            working_dir=str(self.working_dir),
        )
        app.synth()

    @staticmethod
    @override
    def get_required_config_keys() -> list[str]:
        """Get the list of required configuration keys for GCP.

        Returns:
            List of required configuration keys
        """
        return ["project"]

    @staticmethod
    @override
    def validate_config(config: dict[str, Any]) -> None:  # pyright: ignore[reportExplicitAny]
        """Validate GCP configuration.

        Args:
            config: GCP configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required keys
        required_keys = GCPProvider.get_required_config_keys()
        for key in required_keys:
            if key not in config:
                msg = f"Missing required GCP configuration key: {key}"
                raise ValueError(msg)

        # Validate project ID
        GCPProvider._validate_project_id(config["project"])

        # Validate optional string keys
        optional_keys = ["region", "service_name", "artifact_repository_id"]
        for key in optional_keys:
            if key in config:
                GCPProvider._validate_string_field(config[key], key)

    @staticmethod
    def _validate_project_id(project_id: Any) -> None:  # noqa: ANN401  # pyright: ignore[reportAny,reportExplicitAny]
        """Validate project ID field.

        Raises:
            TypeError: If project ID is not a string
            ValueError: If project ID is empty
        """
        if not isinstance(project_id, str):
            msg = "GCP project ID must be a string"
            raise TypeError(msg)
        if not project_id.strip():
            msg = "GCP project ID cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _validate_string_field(value: Any, field_name: str) -> None:  # noqa: ANN401  # pyright: ignore[reportAny,reportExplicitAny]
        """Validate a string field.

        Raises:
            TypeError: If value is not a string
        """
        if not isinstance(value, str):
            msg = f"GCP {field_name} must be a string; got {value}"
            raise TypeError(msg)
