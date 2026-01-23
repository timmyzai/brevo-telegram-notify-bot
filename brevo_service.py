from enum import Enum
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DYNAMODB_TABLE_NAME

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


class EventsEnum(str, Enum):
    DELIVERED = "delivered"
    REQUEST = "request"
    CLICK = "click"
    OPENED = "opened"
    UNIQUE_OPENED = "uniqueOpened"
    LIST_ADDITION = "listAddition"
    CONTACT_UPDATED = "contactUpdated"
    CONTACT_DELETED = "contactDeleted"
    INBOUND_EMAIL_PROCESSED = "inboundEmailProcessed"
    SENT = "sent"
    HARD_BOUNCE = "hardBounce"
    SOFT_BOUNCE = "softBounce"
    BLOCKED = "blocked"
    SPAM = "spam"
    INVALID = "invalid"
    DEFERRED = "deferred"
    UNSUBSCRIBED = "unsubscribed"


def try_mark_email_processed(email: str, event_type: str) -> bool:
    """Atomically mark an email+event as processed. Returns True if new, False if already existed."""
    try:
        table.put_item(
            Item={
                "email": email,
                "event_type": event_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(email) AND attribute_not_exists(event_type)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        print(f"Error writing to DynamoDB:", e)
        return False


def send_telegram_message(message: str):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print("Error sending Telegram message:", e)
        return None

def process_generic_event(event_type: EventsEnum, data: dict):
    email = data.get("email")
    if not email:
        return {"status": "error", "message": "Missing email field"}, 400

    if not try_mark_email_processed(email, event_type.value):
        print(f"{event_type.value} email already processed:", email)
        return {"status": "success", "message": "Email already processed"}, 200

    tags = data.get("tags", [])
    environment = tags[0] if tags else "unknown"

    message_lines = [
        f"📩 **New {event_type.value.capitalize()} Event Detected**",
        f"📧 Email: {email}",
        f"💬 Subject: {data.get('subject')}",
        f"📅 Timestamp: {data.get('date')}",
        f"🏷️ Environment: {environment}"
    ]

    reason = data.get("reason")
    if reason:
        message_lines.append(f"❗ Reason: {reason}")

    send_telegram_message("\n".join(message_lines))
    print(f"Notified new {event_type.value} email:", email)

    return {
        "status": "success",
        "message": f"{event_type.value} email notified",
    }, 200

def handle_event(data):
    """Route events to dynamic processor."""
    event = data.get("event")
    if not event:
        return {"status": "error", "message": "Missing event field"}, 400

    try:
        event_type = EventsEnum(event)
    except ValueError:
        return {"status": "ignored", "message": "Unhandled event"}, 200

    return process_generic_event(event_type, data)
