output "pubsub_topic_name" {
  value = google_pubsub_topic.feedback_topic.name
}

output "positive_subscription_name" {
  value = google_pubsub_subscription.positive_sub.name
}

output "negative_subscription_name" {
  value = google_pubsub_subscription.negative_sub.name
}

output "receiver_function_url" {
  value       = google_cloudfunctions_function.receiver_function.https_trigger_url
  description = "The URL of the receiver function"
}

output "feedback_topic" {
  value       = google_pubsub_topic.feedback_topic.name
  description = "The name of the feedback topic"
}

output "positive_subscription" {
  value       = google_pubsub_subscription.positive_sub.name
  description = "The name of the positive feedback subscription"
}

output "negative_subscription" {
  value       = google_pubsub_subscription.negative_sub.name
  description = "The name of the negative feedback subscription"
}