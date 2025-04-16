terraform {
  backend "gcs" {
    # bucket and prefix will be set by GitHub Actions
  }
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "google" {
  # Credentials and project ID will be provided by GitHub Actions environment
}

# BigQuery dataset conditionally created based on variable
resource "google_bigquery_dataset" "mt5_trading" {
  count = var.create_bigquery_dataset ? 1 : 0
  
  dataset_id = "mt5_trading"
  location   = var.region
  description = "MT5 Trading data"
  
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      labels,
      access,
      default_table_expiration_ms
    ]
  }
}


# Storage bucket for Cloud Functions source code
# Storage bucket for Cloud Functions source code
resource "google_storage_bucket" "function_bucket" {
  count = var.create_storage_bucket ? 1 : 0
  
  name     = "${var.project_id}-function-bucket"
  location = var.region
  uniform_bucket_level_access = true
  
  lifecycle {
    # Remove the prevent_destroy setting for now
    # prevent_destroy = true
    
    # Instead, ignore changes to avoid recreation
    ignore_changes = [
      labels,
      storage_class,
      versioning,
      website,
      cors,
      logging,
      lifecycle_rule
    ]
  }
}


# Pub/Sub topic for MT5 updates
resource "google_pubsub_topic" "mt5_topic" {
  count = var.create_pubsub_topic ? 1 : 0
  
  name = "mt5-trading-topic"
  
  lifecycle {
    #prevent_destroy = true
    ignore_changes = [
      labels,
      kms_key_name,
      message_retention_duration
    ]
  }
}

# BigQuery tables
resource "google_bigquery_table" "positions" {
  count = var.create_bigquery_dataset ? 1 : 0
  dataset_id = google_bigquery_dataset.mt5_trading[0].dataset_id
  table_id   = "positions"

  schema = jsonencode([
    {
      name = "timestamp",
      type = "TIMESTAMP",
      mode = "REQUIRED"
    },
    # Add other fields as needed
  ])
}

resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.mt5_trading[0].dataset_id
  table_id   = "transactions"

  schema = jsonencode([
    {
      name = "timestamp",
      type = "TIMESTAMP",
      mode = "REQUIRED"
    },
    {
      name = "ticket",
      type = "INTEGER",
      mode = "REQUIRED"
    },
    {
      name = "type",
      type = "STRING",
      mode = "REQUIRED"
    },
    {
      name = "symbol",
      type = "STRING",
      mode = "REQUIRED"
    },
    {
      name = "volume",
      type = "FLOAT",
      mode = "REQUIRED"
    },
    {
      name = "price",
      type = "FLOAT",
      mode = "REQUIRED"
    },
    {
      name = "commission",
      type = "FLOAT",
      mode = "NULLABLE"
    },
    {
      name = "swap",
      type = "FLOAT",
      mode = "NULLABLE"
    },
    {
      name = "profit",
      type = "FLOAT",
      mode = "REQUIRED"
    }
  ])
}

resource "google_bigquery_table" "price_updates" {
  dataset_id = google_bigquery_dataset.mt5_trading[0].dataset_id
  table_id   = "price_updates"

  schema = jsonencode([
    {
      name = "timestamp",
      type = "TIMESTAMP",
      mode = "REQUIRED"
    },
    {
      name = "symbol",
      type = "STRING",
      mode = "REQUIRED"
    },
    {
      name = "bid",
      type = "FLOAT",
      mode = "REQUIRED"
    },
    {
      name = "ask",
      type = "FLOAT",
      mode = "REQUIRED"
    },
    {
      name = "spread",
      type = "FLOAT",
      mode = "REQUIRED"
    }
  ])
}

# Create a zip archive of the function source
data "archive_file" "http_function_source" {
  type        = "zip"
  output_path = "${path.module}/http_function.zip"
  source_dir  = "../function_deploy/http_function"
}

data "archive_file" "pubsub_function_source" {
  type        = "zip"
  output_path = "${path.module}/pubsub_function.zip"
  source_dir  = "../function_deploy/pubsub_function"
}

# Upload the function source to the bucket
# Upload the function source to the bucket - only create if bucket exists
resource "google_storage_bucket_object" "http_function_zip" {
  count  = var.create_storage_bucket ? 1 : 0
  
  name   = "http_function-${data.archive_file.http_function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket[0].name
  source = data.archive_file.http_function_source.output_path
}

resource "google_storage_bucket_object" "pubsub_function_zip" {
  count  = var.create_storage_bucket ? 1 : 0
  
  name   = "pubsub_function-${data.archive_file.pubsub_function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket[0].name
  source = data.archive_file.pubsub_function_source.output_path
}

# HTTP Function (Gen 2)
resource "google_cloudfunctions2_function" "http_function" {
  count = var.create_http_function && var.create_storage_bucket ? 1 : 0


  name        = "mt5-http-function"
  location    = var.region
  description = "HTTP function for processing MT5 trading data"

  build_config {
    runtime     = "python310"
    entry_point = "process_mt5_data"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket[0].name
        object = google_storage_bucket_object.http_function_zip[0].name  # Add [0] index here
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "${var.cloud_function_memory}M"
    timeout_seconds    = var.cloud_function_timeout
    environment_variables = {
      PROJECT_ID = var.project_id
      BQ_DATASET = var.bigquery_dataset
    }
    ingress_settings               = "ALLOW_ALL"
    all_traffic_on_latest_revision = true
    service_account_email          = var.service_account_email
  }
}
# HTTP Function IAM
resource "google_cloud_run_service_iam_member" "http_invoker" {
  count = var.create_http_function ? 1 : 0
  
  location = google_cloudfunctions2_function.http_function[0].location
  service  = google_cloudfunctions2_function.http_function[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"  # Makes the function publicly accessible
}

# Pub/Sub Function (Gen 2)
resource "google_cloudfunctions2_function" "pubsub_function" {
  count = var.create_pubsub_function ? 1 : 0

  name        = "mt5-pubsub-function"
  location    = var.region
  description = "Pub/Sub function for processing MT5 trading data"

  build_config {
    runtime     = "python310"
    entry_point = "pubsub_function"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket[0].name
        object = google_storage_bucket_object.pubsub_function_zip[0].name  # Add [0] index here
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "${var.cloud_function_memory}M"
    timeout_seconds    = var.cloud_function_timeout
    environment_variables = {
      PROJECT_ID = var.project_id
      BQ_DATASET = var.bigquery_dataset
    }
    service_account_email = var.service_account_email
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.mt5_topic[0].id
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}

# Grant BigQuery access to the service account
resource "google_project_iam_member" "function_bigquery_access" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${var.service_account_email}"
}