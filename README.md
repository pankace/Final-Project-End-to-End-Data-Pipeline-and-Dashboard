# Sentiment Analysis Pipeline

This project implements a sentiment analysis pipeline using Google Cloud Functions and Pub/Sub to process user feedback messages. The pipeline analyzes sentiment using the Google Cloud Natural Language API and sends alerts to Slack based on the sentiment category.

## Project Structure

```
sentiment-analysis-pipeline
├── functions
│   ├── pubsub-receiver
│   │   ├── main.py          # Receiver Function implementation
│   │   └── requirements.txt  # Dependencies for Receiver Function
│   ├── pubsub-positive-analyzer
│   │   ├── main.py          # Positive Analyzer Function implementation
│   │   └── requirements.txt  # Dependencies for Positive Analyzer Function
│   └── pubsub-negative-analyzer
│       ├── main.py          # Negative Analyzer Function implementation
│       └── requirements.txt  # Dependencies for Negative Analyzer Function
├── terraform
│   ├── main.tf              # Terraform configuration for infrastructure
│   ├── variables.tf         # Variables for Terraform configuration
│   └── outputs.tf           # Outputs of the Terraform configuration
├── tests
│   └── test_functions.py     # Unit tests for the functions
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
└── README.md                 # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd sentiment-analysis-pipeline
   ```

2. **Set up Google Cloud:**
   - Create a Google Cloud project.
   - Enable the Google Cloud Pub/Sub and Natural Language APIs.
   - Set up authentication and create a service account with the necessary permissions.

3. **Configure Terraform:**
   - Update the `terraform/variables.tf` file with your project ID and region.
   - Run the following commands to deploy the infrastructure:
     ```
     cd terraform
     terraform init
     terraform apply
     ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in the required values, including the Slack bot token.

5. **Install dependencies:**
   - For each function, navigate to the respective directory and install the required dependencies:
     ```
     cd functions/pubsub-receiver
     pip install -r requirements.txt
     cd ../pubsub-positive-analyzer
     pip install -r requirements.txt
     cd ../pubsub-negative-analyzer
     pip install -r requirements.txt
     ```

## Usage

- **Receiver Function:**
  - Endpoint: `https://us-central1-[PROJECT_ID].cloudfunctions.net/receiver`
  - Method: `POST`
  - Body (JSON):
    - Positive: `{"user_id": "test@example.com", "message": "I love this!"}`
    - Neutral: `{"user_id": "test@example.com", "message": "It’s okay."}`
    - Negative: `{"user_id": "test@example.com", "message": "This isn’t working."}`

- **Expected Behavior:**
  - Positive message → Slack #followup
  - Negative message → Slack #support
  - Neutral message → No action

## Testing

- Unit tests are located in the `tests/test_functions.py` file. You can run the tests using:
  ```
  python -m unittest discover -s tests
  ```

## License

This project is licensed under the MIT License.