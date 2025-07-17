variable "project_id" {
  description = "GCP project where everything will be created"
  type        = string
}

variable "region" {
  description = "GCP region for Artifact Registry & Cloud Run"
  type        = string
  default     = "us-central1"
}

variable "artifact_repository_id" {
  description = "Reusable Docker repo name (won't be destroyed)"
  type        = string
  default     = "emsipi-repo"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "emsipi"
}

variable "container_image_tag" {
  description = "Docker tag to deploy (re‑built on every apply)"
  type        = string
  default     = "latest"
}
