variable "project_id" {
  description = "Your Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region for resources"
  type        = string
  default     = "us-central1"
}

variable "allow_public_access" {
  description = "Whether to allow public access to the cloud function"
  type        = bool
  default     = true
}