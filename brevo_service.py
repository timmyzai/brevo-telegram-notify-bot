import logging
from enum import Enum
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DYNAMODB_TABLE_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Log config at import time (mask bot token)
token_preview = TELEGRAM_BOT_TOKEN[:8] + "..." if TELEGRAM_BOT_TOKEN else "NOT SET"
logger.info(f"Config loaded: TELEGRAM_BOT_TOKEN={token_preview}, TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}, DYNAMODB_TABLE_NAME={DYNAMODB_TABLE_NAME}")


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
        logger.info(f"DynamoDB: marked as processed email={email}, event_type={event_type}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            logger.info(f"DynamoDB: already processed email={email}, event_type={event_type}")
            return False
        logger.error(f"DynamoDB error: {e}")
        return False


def send_telegram_message(message: str):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    logger.info(f"Telegram: sending message to chat_id={TELEGRAM_CHAT_ID}")
    try:
        response = requests.post(url, data=payload, timeout=10)
        result = response.json()
        if not result.get("ok"):
            logger.error(f"Telegram API error: status={response.status_code}, response={result}")
        else:
            msg_id = result.get("result", {}).get("message_id")
            logger.info(f"Telegram: message sent successfully, message_id={msg_id}")
        return result
    except requests.exceptions.Timeout:
        logger.error("Telegram: request timed out")
        return None
    except Exception as e:
        logger.error(f"Telegram: unexpected error: {e}")
        return None


def process_generic_event(event_type: EventsEnum, data: dict):
    email = data.get("email")
    if not email:
        logger.warning("Missing email field in event data")
        return {"status": "error", "message": "Missing email field"}, 400

    if not try_mark_email_processed(email, event_type.value):
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

    return {
        "status": "success",
        "message": f"{event_type.value} email notified",
    }, 200

def handle_event(data):
    """Route events to dynamic processor."""
    event = data.get("event")
    if not event:
        logger.warning("Missing event field in webhook data")
        return {"status": "error", "message": "Missing event field"}, 400

    try:
        event_type = EventsEnum(event)
    except ValueError:
        logger.info(f"Unhandled event type: {event}")
        return {"status": "ignored", "message": "Unhandled event"}, 200

    return process_generic_event(event_type, data)
