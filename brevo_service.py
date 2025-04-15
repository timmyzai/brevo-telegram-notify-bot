from enum import Enum
import json
import os
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENVIRONMENT


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


event_storage = {
    EventsEnum.HARD_BOUNCE: {"file": "hardbounce_emails.json", "emails": set()},
    EventsEnum.SOFT_BOUNCE: {"file": "softbounce_emails.json", "emails": set()},
    EventsEnum.BLOCKED: {"file": "blocked_emails.json", "emails": set()},
    EventsEnum.SPAM: {"file": "spam_emails.json", "emails": set()},
    EventsEnum.INVALID: {"file": "invalid_emails.json", "emails": set()},
    EventsEnum.DEFERRED: {"file": "deferred_emails.json", "emails": set()},
    EventsEnum.UNSUBSCRIBED: {"file": "unsubscribed_emails.json", "emails": set()},
    EventsEnum.SENT: {"file": "sent_emails.json", "emails": set()},
}


def load_event_emails():
    """Load all event emails from their respective JSON files into memory."""
    for event, meta in event_storage.items():
        if os.path.exists(meta["file"]):
            try:
                with open(meta["file"], "r") as f:
                    meta["emails"] = set(json.load(f))
            except Exception as e:
                print(f"Error reading {meta['file']}:", e)
                meta["emails"] = set()
        else:
            meta["emails"].clear()


def save_event_emails(event: EventsEnum):
    """Save emails for a specific event type."""
    meta = event_storage.get(event)
    if meta:
        with open(meta["file"], "w") as f:
            json.dump(list(meta["emails"]), f)


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

    meta = event_storage.get(event_type)
    if not meta:
        return {"status": "ignored", "message": "No processing for this event"}, 200

    if email not in meta["emails"]:
        meta["emails"].add(email)
        save_event_emails(event_type)

        message_lines = [
            f"📩 **New {event_type.value.capitalize()} Event Detected**",
            f"📧 Email: {email}",
            f"💬 Subject: {data.get('subject')}",
            f"📅 Timestamp: {data.get('date')}",
            f"🌐 IP/Sender: {data.get('sending_ip')}"
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
    else:
        print(f"{event_type.value} email already processed:", email)
        return {"status": "success", "message": "Email already processed"}, 200

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
