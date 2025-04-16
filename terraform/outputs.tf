output "mt5_function_url" {
  description = "URL of the deployed MT5 cloud function"
  value       = google_cloudfunctions2_function.mt5_to_bigquery.url
}

output "bigquery_dataset" {
  description = "BigQuery dataset for MT5 data"
  value       = data.google_bigquery_dataset.mt5_trading.dataset_id
}

output "positions_table" {
  description = "BigQuery table for positions data"
  value       = "${data.google_bigquery_dataset.mt5_trading.dataset_id}.${google_bigquery_table.positions.table_id}"
}

output "transactions_table" {
  description = "BigQuery table for transactions data"
  value       = "${data.google_bigquery_dataset.mt5_trading.dataset_id}.${google_bigquery_table.transactions.table_id}"
}

output "prices_table" {
  description = "BigQuery table for price updates data"
  value       = "${data.google_bigquery_dataset.mt5_trading.dataset_id}.${google_bigquery_table.price_updates.table_id}"
}