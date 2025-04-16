# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Check if Pub/Sub topic exists
data "google_pubsub_topic" "existing_topic" {
  count = try(data.google_pubsub_topic.existing_topic[0].name, "") == "feedback-topic" ? 1 : 0
  name  = "feedback-topic"
}

# Create Pub/Sub topic if it doesn't exist
resource "google_pubsub_topic" "feedback_topic" {
  count = length(data.google_pubsub_topic.existing_topic) > 0 ? 0 : 1
  name  = "feedback-topic"
}

# Get the topic name, whether it's existing or newly created
locals {
  topic_name = length(data.google_pubsub_topic.existing_topic) > 0 ? data.google_pubsub_topic.existing_topic[0].name : google_pubsub_topic.feedback_topic[0].name
}

# Check if positive subscription exists
data "google_pubsub_subscription" "existing_positive_sub" {
  count = try(data.google_pubsub_subscription.existing_positive_sub[0].name, "") == "positive-sub" ? 1 : 0
  name  = "positive-sub"
}

# Create positive subscription if it doesn't exist
resource "google_pubsub_subscription" "positive_sub" {
  count = length(data.google_pubsub_subscription.existing_positive_sub) > 0 ? 0 : 1
  name  = "positive-sub"
  topic = local.topic_name
}

# Check if negative subscription exists
data "google_pubsub_subscription" "existing_negative_sub" {
  count = try(data.google_pubsub_subscription.existing_negative_sub[0].name, "") == "negative-sub" ? 1 : 0
  name  = "negative-sub"
}

# Create negative subscription if it doesn't exist
resource "google_pubsub_subscription" "negative_sub" {
  count = length(data.google_pubsub_subscription.existing_negative_sub) > 0 ? 0 : 1
  name  = "negative-sub"
  topic = local.topic_name
}

# Get the subscription names, whether existing or newly created
locals {
  positive_sub_name = length(data.google_pubsub_subscription.existing_positive_sub) > 0 ? data.google_pubsub_subscription.existing_positive_sub[0].name : google_pubsub_subscription.positive_sub[0].name
  negative_sub_name = length(data.google_pubsub_subscription.existing_negative_sub) > 0 ? data.google_pubsub_subscription.existing_negative_sub[0].name : google_pubsub_subscription.negative_sub[0].name
}

# Check if BigQuery dataset exists
data "google_bigquery_dataset" "existing_dataset" {
  count     = try(data.google_bigquery_dataset.existing_dataset[0].dataset_id, "") == "feedback_dataset" ? 1 : 0
  dataset_id = "feedback_dataset"
}

# Create BigQuery dataset if it doesn't exist
resource "google_bigquery_dataset" "feedback_dataset" {
  count     = length(data.google_bigquery_dataset.existing_dataset) > 0 ? 0 : 1
  dataset_id = "feedback_dataset"
  location   = "US"
}

# Get the dataset ID, whether existing or newly created
locals {
  dataset_id = length(data.google_bigquery_dataset.existing_dataset) > 0 ? data.google_bigquery_dataset.existing_dataset[0].dataset_id : google_bigquery_dataset.feedback_dataset[0].dataset_id
}

# Check if BigQuery table exists
data "google_bigquery_table" "existing_table" {
  count      = try(data.google_bigquery_table.existing_table[0].table_id, "") == "feedback_table" ? 1 : 0
  dataset_id = local.dataset_id
  table_id   = "feedback_table"
}

# Create BigQuery table if it doesn't exist
resource "google_bigquery_table" "feedback_table" {
  count     = length(data.google_bigquery_table.existing_table) > 0 ? 0 : 1
  dataset_id = local.dataset_id
  table_id   = "feedback_table"

  schema = jsonencode([
    {
      name = "user_id"
      type = "STRING"
    },
    {
      name = "message"
      type = "STRING"
    }
  ])
}

# Get the table details, whether existing or newly created
locals {
  table_project = length(data.google_bigquery_table.existing_table) > 0 ? data.google_bigquery_table.existing_table[0].project : google_bigquery_table.feedback_table[0].project
  table_id      = length(data.google_bigquery_table.existing_table) > 0 ? data.google_bigquery_table.existing_table[0].table_id : google_bigquery_table.feedback_table[0].table_id
}

# Check if BigQuery subscription exists
data "google_pubsub_subscription" "existing_bigquery_subscription" {
  count = try(data.google_pubsub_subscription.existing_bigquery_subscription[0].name, "") == "bigquery-subscription" ? 1 : 0
  name  = "bigquery-subscription"
}

# Create BigQuery subscription if it doesn't exist
resource "google_pubsub_subscription" "bigquery_subscription" {
  count = length(data.google_pubsub_subscription.existing_bigquery_subscription) > 0 ? 0 : 1
  name  = "bigquery-subscription"
  topic = local.topic_name

  bigquery_config {
    table            = "${local.table_project}.${local.dataset_id}.${local.table_id}"
    use_topic_schema = false
    write_metadata   = true
  }
}

# Check if Secret Manager secret exists
data "google_secret_manager_secret" "existing_slack_token" {
  count     = try(data.google_secret_manager_secret.existing_slack_token[0].secret_id, "") == "slacktoken" ? 1 : 0
  secret_id = "slacktoken"
}

# Create Secret Manager secret if it doesn't exist
resource "google_secret_manager_secret" "slack_token" {
  count     = length(data.google_secret_manager_secret.existing_slack_token) > 0 ? 0 : 1
  secret_id = "slacktoken"
  
  replication {
    automatic = true
  }
}

# Get the secret ID, whether existing or newly created
locals {
  secret_id = length(data.google_secret_manager_secret.existing_slack_token) > 0 ? data.google_secret_manager_secret.existing_slack_token[0].secret_id : google_secret_manager_secret.slack_token[0].secret_id
}

# Service accounts for Cloud Functions
resource "google_service_account" "function_service_account" {
  account_id   = "sentiment-functions-sa"
  display_name = "Sentiment Analysis Functions Service Account"
}

# IAM permissions
resource "google_project_iam_binding" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  
  members = [
    "serviceAccount:${google_service_account.function_service_account.email}",
  ]
}

resource "google_project_iam_binding" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  
  members = [
    "serviceAccount:${google_service_account.function_service_account.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "secret_access" {
  project   = var.project_id
  secret_id = local.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.function_service_account.email}",
  ]
}

# Storage for Cloud Functions source code
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-function-source"
  location = "US"
}

# Zip and upload function source code
data "archive_file" "receiver_source" {
  type        = "zip"
  source_dir  = "${path.module}/../functions/pubsub-receiver"
  output_path = "${path.module}/tmp/receiver.zip"
}

resource "google_storage_bucket_object" "receiver_archive" {
  name   = "receiver-${data.archive_file.receiver_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.receiver_source.output_path
}

data "archive_file" "positive_analyzer_source" {
  type        = "zip"
  source_dir  = "${path.module}/../functions/pubsub-positive-analyzer"
  output_path = "${path.module}/tmp/positive-analyzer.zip"
}

resource "google_storage_bucket_object" "positive_analyzer_archive" {
  name   = "positive-analyzer-${data.archive_file.positive_analyzer_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.positive_analyzer_source.output_path
}

data "archive_file" "negative_analyzer_source" {
  type        = "zip"
  source_dir  = "${path.module}/../functions/pubsub-negative-analyzer"
  output_path = "${path.module}/tmp/negative-analyzer.zip"
}

resource "google_storage_bucket_object" "negative_analyzer_archive" {
  name   = "negative-analyzer-${data.archive_file.negative_analyzer_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.negative_analyzer_source.output_path
}

# Cloud Functions
resource "google_cloudfunctions_function" "receiver_function" {
  name        = "pubsub-receiver"
  description = "Receives feedback and publishes to Pub/Sub"
  runtime     = "python39"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.receiver_archive.name
  trigger_http          = true
  entry_point           = "receive_message"
  service_account_email = google_service_account.function_service_account.email
  
  environment_variables = {
    PUBSUB_TOPIC = local.topic_name
  }
}

resource "google_cloudfunctions_function" "positive_analyzer" {
  name        = "pubsub-positive-analyzer"
  description = "Analyzes positive sentiment and sends Slack alerts"
  runtime     = "python39"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.positive_analyzer_archive.name
  entry_point           = "analyze_sentiment"
  service_account_email = google_service_account.function_service_account.email
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = local.topic_name
  }
  
  secret_environment_variables {
    key     = "SLACK_TOKEN"
    secret  = local.secret_id
    version = "latest"
  }
  
  environment_variables = {
    SLACK_CHANNEL = var.positive_channel_id
    SENTIMENT_THRESHOLD = "0.25"
  }
}

resource "google_cloudfunctions_function" "negative_analyzer" {
  name        = "pubsub-negative-analyzer"
  description = "Analyzes negative sentiment and sends Slack alerts"
  runtime     = "python39"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.negative_analyzer_archive.name
  entry_point           = "analyze_sentiment"
  service_account_email = google_service_account.function_service_account.email
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = local.topic_name
  }
  
  secret_environment_variables {
    key     = "SLACK_TOKEN"
    secret  = local.secret_id
    version = "latest"
  }
  
  environment_variables = {
    SLACK_CHANNEL = var.negative_channel_id
    SENTIMENT_THRESHOLD = "-0.25"
  }
}

# IAM for Cloud Function invoker
resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = var.project_id
  region         = var.region
  cloud_function = google_cloudfunctions_function.receiver_function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"  # This allows public access - restrict in production
}