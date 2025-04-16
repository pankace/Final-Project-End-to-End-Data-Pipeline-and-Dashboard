import os
import json
import base64
import functions_framework
import requests
from google.cloud import language_v1

@functions_framework.cloud_event
def analyze_sentiment(cloud_event):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
        cloud_event (CloudEvent): Event payload.
    """
    # Get the message data
    message = cloud_event.data["message"]
    
    # Decode the data from the Pub/Sub message
    if "data" in message:
        pubsub_data = base64.b64decode(message["data"]).decode("utf-8")
        data = json.loads(pubsub_data)
        
        user_id = data.get("user_id")
        message_text = data.get("message")
        
        if user_id and message_text:
            sentiment = analyze_text_sentiment(message_text)
            threshold = float(os.environ.get('SENTIMENT_THRESHOLD', '-0.25'))
            
            if sentiment and sentiment.score < threshold:
                send_slack_alert(user_id, message_text, sentiment.score)
                return "Negative sentiment detected and slack alert sent"
            
    return "No action taken"

def analyze_text_sentiment(text):
    """Analyzes the sentiment of the text."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    
    try:
        sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment
        return sentiment
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return None

def send_slack_alert(user_id, message, score):
    """Sends an alert to Slack channel."""
    slack_token = os.environ.get('SLACK_TOKEN')
    slack_channel = os.environ.get('SLACK_CHANNEL', '#support')
    
    slack_url = 'https://slack.com/api/chat.postMessage'
    
    headers = {
        'Authorization': f'Bearer {slack_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'channel': slack_channel,
        'text': f'Negative feedback from {user_id}: "{message}" (Score: {score:.2f})'
    }
    
    try:
        response = requests.post(slack_url, headers=headers, json=payload)
        response.raise_for_status()
        return "Slack alert sent successfully"
    except Exception as e:
        print(f"Error sending Slack alert: {e}")
        return None