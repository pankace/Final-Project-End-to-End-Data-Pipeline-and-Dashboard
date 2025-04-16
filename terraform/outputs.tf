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
  value       = var.create_bigquery_dataset ? google_bigquery_dataset.mt5_trading[0].dataset_id : "Dataset not created"
}

output "pubsub_topic_name" {
  description = "The name of the Pub/Sub topic"
  value       = var.create_pubsub_topic ? google_pubsub_topic.mt5_topic[0].name : "Topic not created"
}

output "cloud_function_http_url" {
  description = "The HTTPS URL for the HTTP-triggered Cloud Function"
  value       = var.create_http_function ? google_cloudfunctions2_function.http_function[0].service_config[0].uri : "Function not created"
}

output "cloud_function_pubsub_name" {
  description = "The name of the Pub/Sub-triggered Cloud Function"
  value       = var.create_pubsub_function ? google_cloudfunctions2_function.pubsub_function[0].name : "Function not created"
}

output "cloud_function_bucket_name" {
  description = "The name of the GCS bucket storing function source code"
  value       = var.create_storage_bucket ? google_storage_bucket.function_bucket[0].name : "Bucket not created"
}