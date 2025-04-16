# MT5 Trading Pipeline

## Project Overview
The MT5 Trading Pipeline is an end-to-end data pipeline designed to ingest, process, and visualize trading data from MetaTrader 5 (MT5) using Google Cloud Platform (GCP). This project demonstrates the full data engineering lifecycle, from data ingestion to dashboard visualization.

## Problem Statement
The goal of this project is to build a robust data pipeline that:
- Ingests real-time trading data.
- Stores the data in a data lake.
- Moves the data to a data warehouse.
- Transforms the data to make it analysis-ready.
- Presents meaningful insights through a functional dashboard.

## Data Pipeline Type
This project implements a **streaming pipeline** to ingest real-time data into the data lake. The choice of a streaming pipeline allows for immediate processing and analysis of trading data, which is crucial for timely decision-making in trading environments.

## Key Features
- **Pipeline Reliability**: The code is designed to be robust and reusable, ensuring that it can handle multiple runs without failure.
- **Security Best Practices**: The project follows best practices for managing credentials, access control, and secure data handling.
- **Flexibility and Scalability**: The architecture allows for easy reruns and scaling of the pipeline without major rework.
- **Best Practices Adherence**: The project follows principles of decoupling, modularization, and monitoring.

## Project Structure
- **src/**: Contains the main source code for the pipeline.
  - **config/**: Configuration settings for the project.
  - **connectors/**: Modules for connecting to external services (e.g., BigQuery).
  - **processors/**: Logic for processing incoming data.
  - **cloud_functions/**: Cloud Functions for handling HTTP requests and Pub/Sub messages.
  - **utils/**: Utility functions for logging and other common tasks.
- **dashboard/**: Contains the dashboard application for visualizing processed data.
- **terraform/**: Infrastructure as Code (IaC) configuration for deploying resources on GCP.
- **tests/**: Unit tests for ensuring code quality and reliability.
- **requirements.txt**: Lists project dependencies.
- **Dockerfile**: Instructions for building a Docker image for the project.

## Instructions for Deployment
1. **Clone the Repository**: 
   ```
   git clone <repository-url>
   cd mt5-trading-pipeline
   ```

2. **Set Up Environment**: 
   - Create a virtual environment and activate it.
   - Install dependencies:
     ```
     pip install -r requirements.txt
     ```

3. **Configure Settings**: 
   - Update `src/config/settings.py` with your API keys and database connection strings.

4. **Deploy Infrastructure**: 
   - Navigate to the `terraform` directory and run:
     ```
     terraform init
     terraform apply
     ```

5. **Run the Dashboard**: 
   - Start the dashboard application:
     ```
     python dashboard/app.py
     ```

## Limitations
- The project currently relies on simulated data for testing purposes. Future iterations may include integration with live data sources.
- Ensure that any web scraping complies with the target website's terms of service.

## Final Dashboard
A link to the final dashboard will be provided upon completion of the project.

## Conclusion
This project serves as a comprehensive demonstration of the data engineering lifecycle, showcasing the ability to build a scalable and reliable data pipeline on Google Cloud Platform.