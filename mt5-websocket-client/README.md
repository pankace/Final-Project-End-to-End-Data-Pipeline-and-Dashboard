# MT5 WebSocket Client

This project is a WebSocket client for connecting to an MT5 server to receive real-time price updates for forex symbols. The client is designed to run on Google Cloud Run, utilizing environment variables for configuration and ensuring compatibility with Cloud Run's ephemeral file system.

## Features

- Connects to an MT5 server via WebSockets.
- Receives price updates for specified forex symbols.
- Saves received data to CSV files or optionally to Google Cloud Storage.
- Configured to run in a serverless environment with proper logging and signal handling.

## Project Structure

```
mt5-websocket-client
├── src
│   ├── main.py          # Main logic for the WebSocket client
│   └── utils
│       ├── __init__.py  # Package initializer
│       ├── logging.py    # Logging setup for Cloud Run
│       └── storage.py    # Data storage functions
├── Dockerfile            # Docker image definition
├── requirements.txt      # Project dependencies
├── .env                  # Environment variables for local testing
├── .dockerignore         # Files to ignore when building the Docker image
├── .gitignore            # Files to ignore in version control
├── cloudbuild.yaml       # Google Cloud Build configuration
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mt5-websocket-client
   ```

2. **Create a `.env` file for local testing:**
   Populate the `.env` file with the following variables:
   ```
   MT5_SERVER_URL=<your_mt5_server_url>
   FOREX_SYMBOLS=<comma_separated_symbols>
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application locally:**
   ```bash
   python src/main.py
   ```

## Deployment to Google Cloud Run

To deploy the application to Google Cloud Run, use the following commands:

1. **Build the Docker image:**
   ```bash
   gcloud builds submit --tag gcr.io/<your-project-id>/mt5-websocket-client
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy mt5-websocket-client \
       --image gcr.io/<your-project-id>/mt5-websocket-client \
       --platform managed \
       --region <your-region> \
       --set-env-vars MT5_SERVER_URL=<your_mt5_server_url>,FOREX_SYMBOLS=<comma_separated_symbols> \
       --min-instances 1 \
       --timeout 900 \
       --concurrency 1
   ```

## Logging

Logs can be viewed in the Google Cloud Console under the Cloud Run service logs. Ensure that logging is properly set up in `src/utils/logging.py` to capture relevant information.

## Notes

- The application is designed to handle termination signals gracefully, ensuring that any ongoing processes are completed before shutdown.
- Data storage is managed to be compatible with Cloud Run's ephemeral file system, with options to store data in Google Cloud Storage for persistence.

For further details, refer to the individual file documentation within the project.