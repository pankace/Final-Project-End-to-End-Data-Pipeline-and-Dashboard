if you want to deploy via direct connection use the deploy via direct connection python file on the server side 

if you want to deploy via cloud fuction use the cloud fuction file and deploly that on to cloud fuction and then run it from there 
1 create big qury database 
```sql 
-- Create dataset
CREATE DATASET IF NOT EXISTS mt5_trading;

-- Create positions table
CREATE TABLE IF NOT EXISTS mt5_trading.positions (
    timestamp TIMESTAMP,
    trade_id INT64,
    symbol STRING,
    type STRING,
    volume FLOAT64,
    price FLOAT64,
    profit FLOAT64,
    sl FLOAT64,
    tp FLOAT64
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS mt5_trading.transactions (
    timestamp TIMESTAMP,
    transaction_id INT64,
    symbol STRING,
    type STRING,
    volume FLOAT64,
    price FLOAT64,
    commission FLOAT64,
    swap FLOAT64,
    profit FLOAT64
);

-- Create price updates table
CREATE TABLE IF NOT EXISTS mt5_trading.price_updates (
    timestamp TIMESTAMP,
    symbol STRING,
    bid FLOAT64,
    ask FLOAT64,
    spread FLOAT64
);
```
deploy cloud fuction 
gcloud functions deploy process_mt5_data \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point process_mt5_data

run via cloud function 

python cloud_client.py --server ws://your-mt5-server:8765 --cloud-function https://your-cloud-function-url