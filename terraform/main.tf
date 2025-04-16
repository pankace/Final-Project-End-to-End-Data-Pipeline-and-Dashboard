provider "google" {
  project = var.project_id
  region  = var.region
}

#resource "google_bigquery_dataset" "mt5_trading" {
#  dataset_id = "mt5_trading"
#  location   = var.region
#}
resource "google_bigquery_dataset" "mt5_trading" {
  count = var.create_bigquery_dataset ? 1 : 0
  
  dataset_id = "mt5_trading"
  location   = var.region
}

resource "google_storage_bucket" "function_bucket" {
  count = var.create_storage_bucket ? 1 : 0
  
  name     = "${var.project_id}-function-bucket"
  location = var.region
  uniform_bucket_level_access = true
}

resource "google_pubsub_topic" "mt5_topic" {
  count = var.create_pubsub_topic ? 1 : 0
  
  name = "mt5-trading-topic"
}

resource "google_bigquery_table" "positions" {
  dataset_id = google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "positions"

  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "trade_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "symbol"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "volume"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "price"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "profit"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "sl"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "tp"
      type = "FLOAT"
      mode = "NULLABLE"
    }
  ])
}

resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "transactions"

  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "transaction_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "symbol"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "volume"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "price"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "commission"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "swap"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "profit"
      type = "FLOAT"
      mode = "REQUIRED"
    }
  ])
}

resource "google_bigquery_table" "price_updates" {
  dataset_id = google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "price_updates"

  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "symbol"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "bid"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "ask"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "spread"
      type = "FLOAT"
      mode = "REQUIRED"
    }
  ])
}

# Create a storage bucket for the function source code
#resource "google_storage_bucket" "function_bucket" {
#  name     = "${var.project_id}-cloud-functions"
#  location = var.region
#  uniform_bucket_level_access = true
#}
#
# Create a zip archive of the function source
data "archive_file" "http_function_source" {
  type        = "zip"
  output_path = "${path.module}/http_function.zip"
  
  source_dir = "../function_deploy/http_function"
}

data "archive_file" "pubsub_function_source" {
  type        = "zip"
  output_path = "${path.module}/pubsub_function.zip"
  
  source_dir = "../function_deploy/pubsub_function"
}

# Upload the function source to the bucket
resource "google_storage_bucket_object" "http_function_zip" {
  name   = "http_function-${data.archive_file.http_function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket[0].name
  source = data.archive_file.http_function_source.output_path
}

resource "google_storage_bucket_object" "pubsub_function_zip" {
  name   = "pubsub_function-${data.archive_file.pubsub_function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket[0].name
  source = data.archive_file.pubsub_function_source.output_path
}

#resource "google_pubsub_topic" "mt5_topic" {
#  name = "mt5-trading-topic"
#}

# HTTP Function (Gen 2)
resource "google_cloudfunctions2_function" "http_function" {
  name        = "mt5-http-function"
  location    = var.region
  description = "HTTP function for processing MT5 trading data"

  build_config {
    runtime     = "python310"
    entry_point = "process_mt5_data"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket[0].name
        object = google_storage_bucket_object.http_function_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 5
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
  location = google_cloudfunctions2_function.http_function.location
  service  = google_cloudfunctions2_function.http_function.name
  role     = "roles/run.invoker"
  member   = "allUsers"  # Makes the function publicly accessible
}

# Pub/Sub Function (Gen 2)
resource "google_cloudfunctions2_function" "pubsub_function" {
  name        = "mt5-pubsub-function"
  location    = var.region
  description = "Pub/Sub function for processing MT5 trading data"

  build_config {
    runtime     = "python310"
    entry_point = "pubsub_function"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket[0].name
        object = google_storage_bucket_object.pubsub_function_zip.name
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