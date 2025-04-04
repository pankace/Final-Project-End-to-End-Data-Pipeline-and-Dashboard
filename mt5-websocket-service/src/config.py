server_url = "ws://34.87.87.53:8765"
default_symbols = ["XAUUSD"]
storage_option = "gcs"  # Options: "gcs" for Google Cloud Storage or "bigquery" for BigQuery
data_dir = "price_data"  # Directory for local data storage if needed
save_data = True  # Flag to determine if data should be saved
reconnect_delay = 5  # Initial delay for reconnection attempts in seconds
max_reconnect_delay = 60  # Maximum delay for reconnection attempts in seconds