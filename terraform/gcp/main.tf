############################################################################
# Provider configuration
############################################################################
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

############################################################################
# Re‑usable Artifact Registry repository (one‑time creation)
############################################################################

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.artifact_repository_id
  format        = "DOCKER"
  description   = "Docker repo for ${var.service_name}"
  lifecycle {
    prevent_destroy = true        # don’t blow away images on accidental destroy
  }

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "delete-older-than-30d"
    action = "DELETE"

    condition {
      older_than = "2592000s"   # 30 days
      tag_state  = "ANY"   # tagged or untagged
    }
  }

  cleanup_policies {
    id     = "keep-last-3"
    action = "KEEP"

    most_recent_versions {
      keep_count = 3
    }
  }


}

############################################################################
# Service account for Cloud Run
############################################################################
resource "google_service_account" "run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "SA for Cloud Run service ${var.service_name}"
}

# Allow the service account to pull from Artifact Registry
resource "google_project_iam_member" "run_sa_artifact_reader" {
  role   = "roles/artifactregistry.reader"
  member = "serviceAccount:${google_service_account.run_sa.email}"
  project = var.project_id
}

############################################################################
# Build & push container with Cloud Build
############################################################################

locals {
  # Hash of the Git index ≈ current commit; adjust path as needed
  repo_hash = filesha256("${path.root}/../../.git/index")

  # Use the first 12 chars (like a short SHA)
  tag       = substr(local.repo_hash, 0, 12)

  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository_id}/${var.service_name}"
  full_image = "${local.image_name}:${local.tag}"
}

resource "null_resource" "build_and_push" {
  # Rebuild when the Dockerfile changes
  triggers = {
    dockerfile_hash = filesha256("${path.root}/../../Dockerfile")
    repo_hash       = local.repo_hash
    tag             = local.tag
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud builds submit "../../" \
        --project ${var.project_id} \
        --region ${var.region} \
        --tag ${local.full_image}
    EOT
  }

  depends_on = [google_artifact_registry_repository.repo]
}

############################################################################
# Cloud Run v2 service
############################################################################

resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = local.full_image
      ports { container_port = 8080 }
    }
    service_account = google_service_account.run_sa.email
  }

  depends_on = [null_resource.build_and_push]
}

############################################################################
# (Optional) make the service publicly invokable
############################################################################

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  name = google_cloud_run_v2_service.service.name
  location = google_cloud_run_v2_service.service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
