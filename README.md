# MT5 to BigQuery Data Pipeline

## Project Overview

This project implements an end-to-end data pipeline to stream real-time trading data (prices, positions, transactions) from a MetaTrader 5 (MT5) terminal to Google BigQuery using Google Cloud Platform (GCP) services. The pipeline leverages WebSockets for data extraction, Google Cloud Pub/Sub for messaging, Cloud Functions for processing, and BigQuery for data warehousing. Infrastructure is managed using Terraform, and deployment is automated with GitHub Actions.

## Problem Statement

The goal is to create a reliable, scalable, and automated system to:
1.  Connect to an MT5 terminal and capture real-time price ticks and trade events (positions opened, updated, closed).
2.  Publish this data reliably to a cloud-based messaging system.
3.  Process and transform the incoming data streams.
4.  Store the processed data efficiently in a data warehouse (BigQuery) for analysis and visualization.
5.  Automate the deployment and management of the required cloud infrastructure.

## Architecture

The pipeline follows a streaming architecture:

1.  **MT5 Terminal**: The source of trading data. Requires the MT5 terminal software running.
2.  **MT5 WebSocket Server (`vmside/server.py`)**: Runs on a machine (likely a VM) with access to the MT5 terminal. It connects to MT5 using the `MetaTrader5` library ([`vmside/mt5_base.py`](vmside/mt5_base.py), [`vmside/mt5_trading.py`](vmside/mt5_trading.py)) and exposes a WebSocket endpoint serving price and trade updates.
3.  **Pub/Sub Publisher (`vmside/pubsub_publisher.py`)**: Connects to the MT5 WebSocket Server, subscribes to desired symbols and trade updates, and publishes received messages to a Google Cloud Pub/Sub topic.
4.  **Google Cloud Pub/Sub (`terraform/main.tf`)**: Acts as a scalable, asynchronous message broker decoupling the data source from the processing logic.
5.  **Cloud Function (`src/cloud_functions/pubsub_function.py`)**: A serverless function triggered by new messages on the Pub/Sub topic. It parses the message, processes the data using logic from `src/processors/`, and inserts it into the appropriate BigQuery table using the [`connectors.bigquery_client.BigQueryClient`](src/connectors/bigquery_client.py).
6.  **Google BigQuery (`terraform/main.tf`)**: The data warehouse where price updates, positions, and transactions are stored in separate tables (`price_updates`, `positions`, `transactions`).
7.  **(Optional) Dashboard (`Dockerfile`, `dashboard/`)**: A web application (likely Flask or Dash) can be built to visualize the data stored in BigQuery. The Dockerfile suggests containerization for deployment.
8.  **Terraform (`terraform/`)**: Manages the GCP infrastructure (Pub/Sub topic, BigQuery dataset/tables, Cloud Functions, GCS bucket for function code).
9.  **GitHub Actions (`.github/workflows/deploy-cloud-functions.yml`)**: Automates the deployment of Cloud Functions and potentially other infrastructure changes via Terraform upon code pushes to the main branch.

*Note: An HTTP Cloud Function ([`src/cloud_functions/http_function.py`](src/cloud_functions/http_function.py)) also exists, potentially for direct data ingestion via HTTP requests as an alternative or for testing purposes.*

## Key Features

*   **Real-time Data Ingestion**: Captures and processes data as it happens.
*   **Scalable Architecture**: Leverages GCP managed services (Pub/Sub, Cloud Functions, BigQuery) designed for scalability.
*   **Decoupled Components**: Pub/Sub ensures the data source and processing logic are independent.
*   **Infrastructure as Code (IaC)**: Terraform ([`terraform/main.tf`](terraform/main.tf)) defines and manages cloud resources reproducibly.
*   **Automated Deployment**: GitHub Actions workflow ([`.github/workflows/deploy-cloud-functions.yml`](.github/workflows/deploy-cloud-functions.yml)) handles Cloud Function deployment.
*   **Configuration Management**: Settings are managed via environment variables and configuration files ([`src/config/settings.py`](src/config/settings.py), [`vmside/.example.env`](vmside/.example.env)).
*   **Modularity**: Code is organized into connectors, processors, and utilities.
*   **Testing**: Includes unit tests ([`tests/`](tests/)) for processors and cloud functions.

## Technology Stack

*   **Programming Language**: Python 3.9+
*   **MT5 Integration**: `MetaTrader5` Python package
*   **Real-time Communication**: WebSockets (`websockets` library)
*   **Cloud Platform**: Google Cloud Platform (GCP)
*   **Messaging**: Google Cloud Pub/Sub
*   **Compute**: Google Cloud Functions (Gen 2)
*   **Data Warehouse**: Google BigQuery
*   **Infrastructure Management**: Terraform
*   **CI/CD**: GitHub Actions
*   **Containerization**: Docker (for dashboard)
*   **Dependencies**: See [`requirements.txt`](requirements.txt), [`src/cloud_functions/requirements.txt`](src/cloud_functions/requirements.txt)

## Project Structure

```
.
├── .github/workflows/         # GitHub Actions CI/CD workflows
│   └── deploy-cloud-functions.yml
├── cloud function_old/        # Older version of cloud function (potentially obsolete)
├── designdoc.md               # Initial design notes
├── Dockerfile                 # Docker configuration for the dashboard
├── local tester/              # Script to test WebSocket server locally
│   └── test.py
├── README.md                  # This file
├── requirements.txt           # Main Python dependencies
├── src/                       # Source code for cloud components
│   ├── cloud_functions/       # Cloud Function handlers
│   │   ├── http_function.py
│   │   ├── pubsub_function.py
│   │   └── requirements.txt   # Dependencies for Cloud Functions
│   ├── config/                # Configuration settings
│   │   └── settings.py
│   ├── connectors/            # Connectors to external services
│   │   └── bigquery_client.py
│   ├── processors/            # Data processing logic
│   │   ├── price_processor.py
│   │   └── trade_processor.py
│   └── utils/                 # Utility functions (e.g., logging)
├── terraform/                 # Terraform Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── tests/                     # Unit tests
│   ├── test_cloud_functions.py
│   └── test_processors.py
└── vmside/                    # Code running alongside MT5
    ├── .example.env           # Example environment variables for vmside
    ├── mt5_base.py            # Base MT5 connection logic
    ├── mt5_trading.py         # MT5 trading functions
    ├── pubsub_publisher.py    # Connects WebSocket to Pub/Sub
    └── server.py              # WebSocket server for MT5 data
```

## Setup and Deployment

Deployment involves setting up the GCP infrastructure using Terraform and deploying/running the application components (Cloud Functions and the `vmside` scripts).

### Prerequisites

*   **Software**:
    *   Python 3.9 or higher
    *   Google Cloud SDK (`gcloud`) installed and configured (`gcloud auth login`, `gcloud config set project <YOUR_GCP_PROJECT_ID>`)
    *   Terraform installed
    *   Git installed
    *   Access to a running MetaTrader 5 terminal
*   **GCP**:
    *   A Google Cloud Platform project with Billing enabled.
    *   Required GCP APIs enabled: Cloud Functions, Cloud Build, Pub/Sub, BigQuery, Cloud Storage, IAM, Cloud Run (if using Cloud Functions Gen2).
    *   A GCS bucket created *manually* beforehand to store the Terraform state (e.g., `my-mt5-pipeline-tfstate`). This is crucial for collaboration and tracking infrastructure changes.
    *   A GCP Service Account created with necessary permissions (e.g., BigQuery Data Editor, Pub/Sub Publisher/Subscriber, Cloud Functions Developer, Storage Admin, Service Account User). See roles assigned in [`terraform/main.tf`](terraform/main.tf). Download its JSON key file.
*   **GitHub (for CI/CD)**:
    *   A GitHub repository for your project code.
    *   Secrets configured in the repository settings (if using the provided workflow):
        *   `GCP_PROJECT_ID`: Your Google Cloud Project ID.
        *   `GCP_SA_EMAIL`: The email address of the GCP service account used for deployment.
        *   `GCP_SA_KEY`: The JSON key content of the GCP service account.
        *   `TERRAFORM_STATE_BUCKET`: The name of the GCS bucket created for Terraform state.

### Step 1: Clone Repository and Install Local Dependencies

1.  **Clone Repository**:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Set up Python Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # Note: Cloud Function dependencies are in src/cloud_functions/requirements.txt
    # and handled during their specific deployment.
    ```

### Step 2: Provision Cloud Infrastructure (Terraform)

This phase uses Terraform to create the GCP resources defined in the `terraform/` directory.

1.  **Navigate to Terraform Directory**:
    ```bash
    cd terraform
    ```

2.  **Initialize Terraform (`terraform init`)**:
    *   Download provider plugins and configure the backend state storage.
    ```bash
    terraform init \
      -backend-config="bucket=<YOUR_TERRAFORM_STATE_BUCKET_NAME>" \
      -backend-config="prefix=mt5-pipeline/state" # Optional: path within the bucket
    ```

3.  **Plan the Deployment (`terraform plan`)**:
    *   Preview the changes Terraform will make. Provide values for required variables.
    ```bash
    terraform plan \
      -var="project_id=<YOUR_GCP_PROJECT_ID>" \
      -var="region=us-central1" # Or your preferred region
      -var="service_account_email=<YOUR_GCP_SA_EMAIL>" \
      -var="gcs_bucket_name_for_functions=<UNIQUE_BUCKET_NAME_FOR_FUNCTION_CODE>" \
      -var="pubsub_topic_name=mt5-trading-topic" \
      -var="bq_dataset_id=mt5_trading" \
      -out=tfplan # Save the plan to a file
    ```
    *   Review the output carefully to ensure it matches expectations (creation of Pub/Sub topic, BigQuery dataset/tables, GCS bucket, Cloud Function definitions, etc.).

4.  **Apply the Configuration (`terraform apply`)**:
    *   Execute the plan and create the resources in GCP.
    ```bash
    terraform apply tfplan
    ```
    *   Confirm by typing `yes` when prompted.
    *   This creates the infrastructure but might deploy placeholder or initial versions of the Cloud Functions. The actual function code is typically deployed next.

### Step 3: Deploy Cloud Function Code (via GitHub Actions or Manually)

#### Option A: Automated Deployment via GitHub Actions (Recommended)

The provided workflow ([`.github/workflows/deploy-cloud-functions.yml`](.github/workflows/deploy-cloud-functions.yml)) automates this.

1.  **Ensure Prerequisites**: GitHub repository and secrets are configured as listed in the main prerequisites section.
2.  **Trigger**: Push your code changes (especially updates within `src/cloud_functions/`) to the `main` branch.
3.  **Workflow Execution**: GitHub Actions will automatically:
    *   Checkout the code.
    *   Authenticate to GCP using the service account secrets.
    *   Optionally run `terraform apply` to ensure infrastructure is current.
    *   Package the Cloud Function source code (`src/cloud_functions/`) into zip files.
    *   Upload the zip files to the GCS bucket created by Terraform (`gcs_bucket_name_for_functions`).
    *   Execute `gcloud functions deploy` for each function, pointing to the source code in GCS, setting the entry point, trigger (Pub/Sub topic or HTTP), runtime, and necessary environment variables (`PROJECT_ID`, `BQ_DATASET`).

#### Option B: Manual Deployment using `gcloud`

If not using GitHub Actions, you can deploy manually:

1.  **Authenticate `gcloud`**: Ensure your local `gcloud` is authenticated (`gcloud auth login`) or configured to use the service account key (`gcloud auth activate-service-account --key-file=<PATH_TO_KEY_FILE>`).
2.  **Package Function Code**: Create zip archives for each function. For example, for the Pub/Sub function:
    ```bash
    cd src/cloud_functions
    zip -r pubsub_function_source.zip . -x "*/__pycache__/*" # Exclude cache files
    cd ../..
    ```
3.  **Upload to GCS**: Upload the zip file to the bucket created by Terraform.
    ```bash
    gsutil cp src/cloud_functions/pubsub_function_source.zip gs://<YOUR_FUNCTION_CODE_BUCKET_NAME>/
    ```
4.  **Deploy Function**:
    ```bash
    gcloud functions deploy mt5-pubsub-function \
      --gen2 \
      --region=<YOUR_REGION> \ # e.g., us-central1
      --runtime=python39 \
      --source=gs://<YOUR_FUNCTION_CODE_BUCKET_NAME>/pubsub_function_source.zip \
      --entry-point=pubsub_function \
      --trigger-topic=mt5-trading-topic \
      --set-env-vars=PROJECT_ID=<YOUR_GCP_PROJECT_ID>,BQ_DATASET=mt5_trading
    ```
    *   Repeat for the HTTP function, changing the name, entry point, source zip, and using `--trigger-http --allow-unauthenticated`.

### Step 4: Run `vmside` Components

These scripts connect MT5 to Pub/Sub and need to run continuously on a machine with access to the MT5 terminal and GCP.

1.  **Prerequisites**:
    *   Machine (VM/server/local) with Python 3.9+, network access to MT5 terminal and GCP Pub/Sub API.
    *   MT5 Terminal installed and running.
    *   GCP Service Account key file present on this machine.

2.  **Setup on the `vmside` Machine**:
    *   Clone the repository (if not already done).
    *   Set up Python virtual environment and install requirements (`pip install -r requirements.txt`).
    *   Navigate to the `vmside` directory: `cd vmside`
    *   Create `.env` from `.example.env` and fill in:
        *   `MT5_USER`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_PATH` (path to `terminal64.exe`)
        *   `GOOGLE_APPLICATION_CREDENTIALS`: The *full path* to the downloaded GCP service account JSON key file on *this* machine.
        *   `GOOGLE_CLOUD_PROJECT`: Your GCP Project ID.

3.  **Run the WebSocket Server (`server.py`)**:
   *ammed to use pubsub file later*
    *   Connects to MT5 and serves data locally via WebSocket.
    ```bash
    # In the vmside directory
    python server.py --host 0.0.0.0 --port 8765
    ```
    *   Use `--host 0.0.0.0` to allow connections from other machines (like the publisher if run separately). Use `localhost` if publisher is on the same machine.
    *   **Important**: Keep this process running. Use a process manager like `systemd`, `supervisor`, `screen`, or `tmux` for reliable background operation.

4.  **Run the Pub/Sub Publisher (`pubsub_publisher.py`)**:
    *   Connects to the WebSocket server and forwards messages to GCP Pub/Sub.
    ```bash
    # In the vmside directory
    python pubsub_publisher.py \
      --url ws://<WEBSOCKET_SERVER_IP_OR_HOSTNAME>:8765 \
      --project <YOUR_GCP_PROJECT_ID> \
      --topic mt5-trading-topic
    ```
    *   Replace `<WEBSOCKET_SERVER_IP_OR_HOSTNAME>` with the IP/hostname where `server.py` is listening (e.g., `ws://localhost:8765`).
    *   Ensure `--project` and `--topic` match your GCP setup.
    *   **Important**: This also needs to run continuously. Use a process manager.

## Usage

Once all components are deployed and running:

1.  Ensure the MT5 terminal is active.
2.  Ensure `vmside/server.py` is running and connected to MT5.
3.  Ensure `vmside/pubsub_publisher.py` is running and connected to both the WebSocket server and Pub/Sub.
4.  As price ticks and trade events occur in MT5, they will flow through the pipeline: MT5 -> `server.py` -> `pubsub_publisher.py` -> Pub/Sub Topic -> `pubsub_function` Cloud Function -> BigQuery Tables.
5.  Query the `price_updates`, `positions`, and `transactions` tables in the BigQuery console or connect BI tools (Looker Studio, Tableau, etc.) for analysis and visualization.
6.  The `local tester/test.py` script can connect directly to the `server.py` WebSocket for debugging.

## Configuration Details

*   **`vmside/.env`**: Contains MT5 credentials and GCP service account path for the publisher components.
*   **`src/config/settings.py`**: Defines BigQuery table names. Relies on `PROJECT_ID` and `BQ_DATASET` environment variables set in the Cloud Function runtime (configured via Terraform or `gcloud deploy`).
*   **`terraform/variables.tf`**: Defines input variables for Terraform (project ID, region, names, etc.).
*   **GitHub Actions Workflow**: Uses repository secrets for sensitive deployment credentials.

## Testing

Unit tests are located in the `tests/` directory. Run them using `pytest`:

```bash
pip install pytest pytest-mock # If not already installed
pytest tests/
```

## Contributing

Please follow standard Gitflow practices. Create feature branches, write tests for new functionality, and open pull requests for review.