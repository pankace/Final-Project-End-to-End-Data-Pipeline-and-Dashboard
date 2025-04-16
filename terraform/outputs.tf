output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "bigquery_dataset" {
  description = "The BigQuery dataset ID"
  value       = google_bigquery_dataset.mt5_trading[0].dataset_id
}

output "pubsub_topic_name" {
  description = "The name of the Pub/Sub topic"
  value       = google_pubsub_topic.mt5_topic[0].name
}

output "cloud_function_http_url" {
  description = "The HTTPS URL for the HTTP-triggered Cloud Function"
  # Use the correct resource type and attribute for Gen 2 functions
  value = google_cloudfunctions2_function.http_function.service_config[0].uri
}

output "cloud_function_pubsub_name" {
  description = "The name of the Pub/Sub-triggered Cloud Function"
  # Use the correct resource type
  value = google_cloudfunctions2_function.pubsub_function.name
}

output "cloud_function_bucket_name" {
  description = "The name of the GCS bucket storing function source code"
  value       = google_storage_bucket.function_bucket[0].name
}