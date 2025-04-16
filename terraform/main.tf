provider "google" {
  project = var.project_id
  region  = var.region
}

# Create a storage bucket for the cloud function source code
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-function-source"
  location = "US"
  uniform_bucket_level_access = true
}

# Create zip archive of the cloud function
data "archive_file" "mt5_to_cloudfunction" {
  type        = "zip"
  source_dir  = "${path.root}/../functions/mt5 to cloudfunction"
  output_path = "${path.root}/tmp/mt5_to_cloudfunction.zip"
}

# Upload the function source code to the bucket
resource "google_storage_bucket_object" "mt5_function_zip" {
  name   = "source/mt5_to_cloudfunction_${data.archive_file.mt5_to_cloudfunction.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.mt5_to_cloudfunction.output_path
}

# Create BigQuery dataset
resource "google_bigquery_dataset" "mt5_trading" {
  dataset_id  = "mt5_trading"
  description = "Dataset for MT5 trading data"
  location    = "US"
}

# Create BigQuery tables
resource "google_bigquery_table" "positions" {
  dataset_id = google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "positions"

  schema = <<EOF
[
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "trade_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "symbol",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "type",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "volume",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "price",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "profit",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "sl",
    "type": "FLOAT",
    "mode": "NULLABLE"
  },
  {
    "name": "tp",
    "type": "FLOAT",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "transactions"

  schema = <<EOF
[
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "transaction_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "symbol",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "type",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "volume",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "price",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "commission",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "swap",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "profit",
    "type": "FLOAT",
    "mode": "REQUIRED"
  }
]
EOF
}

resource "google_bigquery_table" "price_updates" {
  dataset_id = google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "price_updates"

  schema = <<EOF
[
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "symbol",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "bid",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "ask",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "spread",
    "type": "FLOAT",
    "mode": "REQUIRED"
  }
]
EOF
}

# Create service account for the function
resource "google_service_account" "function_account" {
  account_id   = "mt5-function-sa"
  display_name = "MT5 Cloud Function Service Account"
}

# Grant BigQuery data editor role to the service account
resource "google_project_iam_binding" "function_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"

  members = [
    "serviceAccount:${google_service_account.function_account.email}",
  ]
}

# Deploy the cloud function
resource "google_cloudfunctions2_function" "mt5_to_bigquery" {
  name        = "mt5-to-bigquery"
  location    = var.region
  description = "Function that receives MT5 data and inserts it into BigQuery"

  build_config {
    runtime     = "python39"
    entry_point = "receive_message"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.mt5_function_zip.name
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "256M"
    timeout_seconds       = 60
    service_account_email = google_service_account.function_account.email
    environment_variables = {
      BQ_DATASET           = "mt5_trading"
      BQ_POSITIONS_TABLE   = "positions"
      BQ_TRANSACTIONS_TABLE = "transactions"
      BQ_PRICES_TABLE      = "price_updates"
    }
  }
  
  trigger {
    http {
      security_level = "SECURE_ALWAYS" # HTTP call needs authentication
      cors {
        allow_origin = ["*"]
        allow_methods = ["GET", "POST", "OPTIONS"]
        allow_headers = ["Content-Type", "Authorization"]
        max_age = 3600
      }
    }
  }

  depends_on = [
    google_bigquery_dataset.mt5_trading,
    google_bigquery_table.positions,
    google_bigquery_table.transactions,
    google_bigquery_table.price_updates
  ]
}

# Allow public access to the function (optional - use with caution)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = var.region
  service  = google_cloudfunctions2_function.mt5_to_bigquery.name
  role     = "roles/run.invoker"
  member   = "allUsers"
  
  depends_on = [
    google_cloudfunctions2_function.mt5_to_bigquery
  ]
}