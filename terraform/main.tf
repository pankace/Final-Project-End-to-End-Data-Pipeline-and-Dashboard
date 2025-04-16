provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_bigquery_dataset" "mt5_trading" {
  dataset_id = "mt5_trading"
  location   = var.region
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

resource "google_pubsub_topic" "mt5_topic" {
  name = "mt5_topic"
}

resource "google_cloudfunctions_function" "http_function" {
  name        = "http_function"
  runtime     = "python39"
  entry_point = "process_mt5_data"
  source_archive_bucket = var.source_bucket
  source_archive_object = var.source_object
  trigger_http = true
}

resource "google_cloudfunctions_function" "pubsub_function" {
  name        = "pubsub_function"
  runtime     = "python39"
  entry_point = "process_mt5_pubsub"
  source_archive_bucket = var.source_bucket
  source_archive_object = var.source_object
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.mt5_topic.id
  }
}