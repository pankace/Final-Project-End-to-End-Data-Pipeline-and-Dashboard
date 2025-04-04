# MT5 WebSocket Service

This project implements a WebSocket client that connects to an MT5 server to collect financial data continuously. The collected data is stored in Google Cloud Storage or BigQuery for further analysis.

## Project Structure

```
mt5-websocket-service
├── src
│   ├── main.py              # Entry point of the application
│   ├── websocket_client.py   # Implementation of the MT5WebSocketClient class
│   ├── storage_handler.py    # Manages interactions with Google Cloud Storage or BigQuery
│   └── config.py            # Configuration settings for the application
├── Dockerfile                # Defines the environment for the application
├── requirements.txt          # Lists Python dependencies required for the project
├── .dockerignore             # Specifies files to ignore when building the Docker image
├── .gcloudignore             # Specifies files to ignore when deploying to Google Cloud
└── cloudbuild.yaml           # Configuration for Google Cloud Build
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd mt5-websocket-service
   ```

2. **Install Dependencies**
   Ensure you have Python 3.7 or higher installed. Then, install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Application**
   Update the `src/config.py` file with your MT5 server URL, symbols to subscribe to, and storage options.

4. **Build the Docker Image**
   Use the following command to build the Docker image:
   ```bash
   docker build -t mt5-websocket-service .
   ```

5. **Run the Docker Container**
   You can run the container locally to test it:
   ```bash
   docker run -d -p 8080:8080 mt5-websocket-service
   ```

## Usage

Once the service is running, it will connect to the specified MT5 server and start collecting data. The data will be stored in the configured Google Cloud Storage bucket or BigQuery dataset.

## Deployment

To deploy the application to Google Cloud Run, use the following command:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.