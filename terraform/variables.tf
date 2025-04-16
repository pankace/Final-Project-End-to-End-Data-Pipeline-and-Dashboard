variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "bigquery_dataset" {
  description = "The BigQuery dataset name"
  type        = string
  default     = "mt5_trading"
}

variable "service_account_email" {
  description = "The service account email for Cloud Functions"
  type        = string
}

variable "create_bigquery_dataset" {
  description = "Whether to create a BigQuery dataset"
  type        = bool
  default     = true
}

variable "create_storage_bucket" {
  description = "Whether to create a storage bucket for functions"
  type        = bool
  default     = true
}

variable "create_pubsub_topic" {
  description = "Whether to create a Pub/Sub topic"
  type        = bool
  default     = true
}

variable "cloud_function_memory" {
  description = "Memory allocated to Cloud Functions (in MB)"
  type        = number
  default     = 256
}

variable "cloud_function_timeout" {
  description = "Timeout for Cloud Functions (in seconds)"
  type        = number
  default     = 60
}

variable "create_http_function" {
  description = "Whether to create HTTP Cloud Function"
  type        = bool
  default     = true
}

variable "create_pubsub_function" {
  description = "Whether to create PubSub Cloud Function"
  type        = bool
  default     = true
}