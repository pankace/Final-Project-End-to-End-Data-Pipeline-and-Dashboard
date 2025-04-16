variable "project_id" {
  description = "The ID of the Google Cloud project"
  type        = string
}

variable "region" {
  description = "The region where resources will be deployed"
  type        = string
  default     = "us-central1"
}

variable "slack_token" {
  description = "Slack bot token for sending alerts"
  type        = string
}

variable "feedback_topic" {
  description = "The name of the Pub/Sub topic for feedback messages"
  type        = string
  default     = "feedback-topic"
}

variable "positive_subscription" {
  description = "The name of the subscription for positive feedback"
  type        = string
  default     = "positive-sub"
}

variable "negative_subscription" {
  description = "The name of the subscription for negative feedback"
  type        = string
  default     = "negative-sub"
}


variable "positive_channel_id" {
  description = "Slack channel ID for positive sentiment alerts"
  type        = string
  default     = "C08KN71G5S7"
}

variable "negative_channel_id" {
  description = "Slack channel ID for negative sentiment alerts"
  type        = string
  default     = "CH83QLHLY"
}