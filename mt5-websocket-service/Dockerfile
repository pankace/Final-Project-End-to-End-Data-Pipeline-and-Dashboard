FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/

# Set the environment variable for the entry point
ENV PYTHONPATH=/app
ENV MT5_SERVER_URL="ws://34.87.87.53:8765"
ENV MT5_SYMBOLS="XAUUSD"
ENV STORAGE_TYPE="gcs"
ENV GCS_BUCKET_NAME="mt5-price-data"
ENV BQ_DATASET_ID="mt5_data"
ENV BQ_TABLE_ID="price_data"

# Command to run the application
CMD ["python", "src/main.py"]