import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    BIGQUERY_PROJECT = os.environ.get('BIGQUERY_PROJECT', 'your_project_id')
    BIGQUERY_DATASET = os.environ.get('BIGQUERY_DATASET', 'mt5_trading')
    # BigQuery settings
    BQ_PROJECT_ID = "your-project-id"  # Replace with your actual project ID or use env vars
    BQ_DATASET_ID = "mt5_trading"
    BQ_POSITIONS_TABLE = "positions"
    BQ_TRANSACTIONS_TABLE = "transactions" 
    BQ_PRICES_TABLE = "price_updates"
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'path/to/your/credentials.json')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True

class ProductionConfig(Config):
    """Production configuration."""
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}