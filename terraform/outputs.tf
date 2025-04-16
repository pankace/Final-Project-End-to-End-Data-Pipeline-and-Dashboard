output "bigquery_dataset_id" {
  value = google_bigquery_dataset.mt5_trading.dataset_id
}

output "bigquery_positions_table_id" {
  value = google_bigquery_table.positions.table_id
}

output "bigquery_transactions_table_id" {
  value = google_bigquery_table.transactions.table_id
}

output "bigquery_prices_table_id" {
  value = google_bigquery_table.price_updates.table_id
}

output "cloud_function_http_url" {
  value = google_cloudfunctions_function.http_function.https_trigger_url
}

output "cloud_function_pubsub_name" {
  value = google_cloudfunctions_function.pubsub_function.name
}