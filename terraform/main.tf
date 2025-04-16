provider "google" {
  project = var.project_id
  region  = var.region
}

# Use data sources to reference existing resources instead of creating them
data "google_storage_bucket" "function_bucket" {
  name = "${var.project_id}-function-source"
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
  bucket = data.google_storage_bucket.function_bucket.name
  source = data.archive_file.mt5_to_cloudfunction.output_path
}



// Existing dataset
data "google_bigquery_dataset" "mt5_trading" {
  dataset_id = "mt5_trading"
  project    = var.project_id
}

// ---------------------------------------
// DATA Resources for existing tables
// ---------------------------------------
data "google_bigquery_table" "positions" {
  dataset_id = data.google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "positions"
  project    = var.project_id
}

data "google_bigquery_table" "transactions" {
  dataset_id = data.google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "transactions"
  project    = var.project_id
}

data "google_bigquery_table" "price_updates" {
  dataset_id = data.google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "price_updates"
  project    = var.project_id
}


# Create or update BigQuery tables
resource "google_bigquery_table" "positions" {
  dataset_id = data.google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "positions"
  project    = var.project_id
  deletion_protection = false # Set to true in production

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
  lifecycle {
    ignore_changes = [
      schema,
      time_partitioning,
      clustering
    ]
  }
}

resource "google_bigquery_table" "transactions" {
  dataset_id = data.google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "transactions"
  project    = var.project_id
  deletion_protection = false # Set to true in production

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
  lifecycle {
    ignore_changes = [
      schema,
      time_partitioning,
      clustering
    ]
  }
}

resource "google_bigquery_table" "price_updates" {
  dataset_id = data.google_bigquery_dataset.mt5_trading.dataset_id
  table_id   = "price_updates"
  project    = var.project_id
  deletion_protection = false # Set to true in production

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
  lifecycle {
    ignore_changes = [
      schema,
      time_partitioning,
      clustering
    ]
  }
}

# Use data source to reference existing service account
data "google_service_account" "function_account" {
  account_id = "mt5-function-sa"
  project    = var.project_id # Add project ID for clarity
}

# We'll use additive IAM bindings to avoid conflicts
resource "google_project_iam_member" "function_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${data.google_service_account.function_account.email}"
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
        bucket = data.google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.mt5_function_zip.name
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "256M"
    timeout_seconds       = 60
    service_account_email = data.google_service_account.function_account.email
    environment_variables = {
      BQ_DATASET            = data.google_bigquery_dataset.mt5_trading.dataset_id
      BQ_POSITIONS_TABLE    = google_bigquery_table.positions.table_id
      BQ_TRANSACTIONS_TABLE = google_bigquery_table.transactions.table_id
      BQ_PRICES_TABLE       = google_bigquery_table.price_updates.table_id
    }
    ingress_settings      = "ALLOW_ALL"
    all_traffic_on_latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      labels["deployment-tool"]
    ]
  }
}

# Public access to Cloud Function
resource "google_cloud_run_service_iam_member" "public_invoke" {
  location = var.region
  service  = google_cloudfunctions2_function.mt5_to_bigquery.name
  role     = "roles/run.invoker"
  member   = "allUsers"
  
  depends_on = [
    google_cloudfunctions2_function.mt5_to_bigquery
  ]
}