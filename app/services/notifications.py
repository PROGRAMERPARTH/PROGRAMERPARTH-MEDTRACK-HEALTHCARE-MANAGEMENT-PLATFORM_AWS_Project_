class NotificationService:
    def __init__(self, repository, config):
        self.repository = repository
        self.topic_arn = config.get("SNS_TOPIC_ARN")
        self.region = config.get("AWS_REGION")

    def send(self, user_id, notification_type, title, message):
        notification = self.repository.create_notification(user_id, notification_type, title, message)
        # SNS is intentionally opt-in: configured EC2 roles publish via Boto3,
        # while local development always keeps a visible in-app notification.
        if self.topic_arn:
            try:
                import boto3
                boto3.client("sns", region_name=self.region).publish(TopicArn=self.topic_arn, Subject=title[:100], Message=message)
            except Exception:
                # External delivery failure must not lose the in-app event.
                pass
        return notification
