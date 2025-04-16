variable "project_id" {
  description = "The ID of the Google Cloud project"
  type        = string
}

variable "region" {
  description = "The region where resources will be deployed"
  type        = string
  default     = "us-central1"
}

variable "bigquery_dataset" {
  description = "The name of the BigQuery dataset"
  type        = string
  default     = "mt5_trading"
}

variable "cloud_function_memory" {
  description = "The amount of memory allocated for the Cloud Functions"
  type        = number
  default     = 256
}

variable "cloud_function_timeout" {
  description = "The timeout for the Cloud Functions in seconds"
  type        = number
  default     = 60
}

variable "pubsub_topic" {
  description = "The name of the Pub/Sub topic"
  type        = string
  default     = "mt5-trading-topic"
}

variable "service_account_email" {
  description = "The email of the service account used for authentication"
  type        = string
}