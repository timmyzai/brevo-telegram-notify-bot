import json
import os
import requests
from enum import Enum
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Define the events enum
class EventsEnum(Enum):
    SENT = "sent"
    HARD_BOUNCE = "hardBounce"
    SOFT_BOUNCE = "softBounce"
    BLOCKED = "blocked"
    SPAM = "spam"
    DELIVERED = "delivered"
    REQUEST = "request"
    CLICK = "click"
    INVALID = "invalid"
    DEFERRED = "deferred"
    OPENED = "opened"
    UNIQUE_OPENED = "uniqueOpened"
    UNSUBSCRIBED = "unsubscribed"
    LIST_ADDITION = "listAddition"
    CONTACT_UPDATED = "contactUpdated"
    CONTACT_DELETED = "contactDeleted"
    INBOUND_EMAIL_PROCESSED = "inboundEmailProcessed"

# File names for processed emails per event type
BLOCKED_EMAILS_FILE = "blocked_emails.json"
SOFT_BOUNCE_FILE = "softbounce_emails.json"
HARD_BOUNCE_FILE = "hardbounce_emails.json"

# Global sets to track processed emails for each event type
blocked_emails = set()
softbounce_emails = set()
hardbounce_emails = set()

def get_updates():
    """Get the latest messages from the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        with open('data.json', 'w') as outfile:
            json.dump(response.json(), outfile)
        return response.json()
    except Exception as e:
        print("Error getting updates:", e)
        return None

def load_blocked_emails():
    global blocked_emails
    if os.path.exists(BLOCKED_EMAILS_FILE):
        with open(BLOCKED_EMAILS_FILE, "r") as f:
            try:
                emails = json.load(f)
                blocked_emails = set(emails)
            except Exception as e:
                print("Error reading blocked emails file:", e)
                blocked_emails = set()
    else:
        blocked_emails.clear()
    return blocked_emails

def save_blocked_emails():
    with open(BLOCKED_EMAILS_FILE, "w") as f:
        json.dump(list(blocked_emails), f)

def load_softbounce_emails():
    global softbounce_emails
    if os.path.exists(SOFT_BOUNCE_FILE):
        with open(SOFT_BOUNCE_FILE, "r") as f:
            try:
                emails = json.load(f)
                softbounce_emails = set(emails)
            except Exception as e:
                print("Error reading soft bounce emails file:", e)
                softbounce_emails = set()
    else:
        softbounce_emails.clear()
    return softbounce_emails

def save_softbounce_emails():
    with open(SOFT_BOUNCE_FILE, "w") as f:
        json.dump(list(softbounce_emails), f)

def load_hardbounce_emails():
    global hardbounce_emails
    if os.path.exists(HARD_BOUNCE_FILE):
        with open(HARD_BOUNCE_FILE, "r") as f:
            try:
                emails = json.load(f)
                hardbounce_emails = set(emails)
            except Exception as e:
                print("Error reading hard bounce emails file:", e)
                hardbounce_emails = set()
    else:
        hardbounce_emails.clear()
    return hardbounce_emails

def save_hardbounce_emails():
    with open(HARD_BOUNCE_FILE, "w") as f:
        json.dump(list(hardbounce_emails), f)

def send_telegram_message(message):
    """Send a message to the operator via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print("Error sending Telegram message:", e)
        return None

def process_blocked_event(data):
    global blocked_emails
    email = data.get("email")
    if not email:
        return {"status": "error", "message": "Missing email field"}, 400

    if email not in blocked_emails:
        blocked_emails.add(email)
        save_blocked_emails()
        message = (
            f"New blocked email detected:\n"
            f"Email: {email}\n"
            f"Reason: {data.get('reason')}\n"
            f"Timestamp: {data.get('date')}"
        )
        send_telegram_message(message)
        print("Notified new blocked email:", email)
        return {"status": "success", "message": "Blocked email notified"}, 200
    else:
        print("Blocked email already processed:", email)
        return {"status": "success", "message": "Email already processed"}, 200

def process_softbounce_event(data):
    global softbounce_emails
    email = data.get("email")
    if not email:
        return {"status": "error", "message": "Missing email field"}, 400

    if email not in softbounce_emails:
        softbounce_emails.add(email)
        save_softbounce_emails()
        message = (
            f"New soft bounce detected:\n"
            f"Email: {email}\n"
            f"Reason: {data.get('reason')}\n"
            f"Timestamp: {data.get('date')}"
        )
        send_telegram_message(message)
        print("Notified new soft bounce:", email)
        return {"status": "success", "message": "Soft bounce notified"}, 200
    else:
        print("Soft bounce already processed:", email)
        return {"status": "success", "message": "Email already processed"}, 200

def process_hardbounce_event(data):
    global hardbounce_emails
    email = data.get("email")
    if not email:
        return {"status": "error", "message": "Missing email field"}, 400

    if email not in hardbounce_emails:
        hardbounce_emails.add(email)
        save_hardbounce_emails()
        message = (
            f"New hard bounce detected:\n"
            f"Email: {email}\n"
            f"Reason: {data.get('reason')}\n"
            f"Timestamp: {data.get('date')}"
        )
        send_telegram_message(message)
        print("Notified new hard bounce:", email)
        return {"status": "success", "message": "Hard bounce notified"}, 200
    else:
        print("Hard bounce already processed:", email)
        return {"status": "success", "message": "Email already processed"}, 200

def handle_event(data):
    """
    Handle an incoming event from Brevo. This function routes the event to the correct
    processing function based on its type (blocked, softBounce, hardBounce).
    """
    event = data.get("event")
    if event == EventsEnum.BLOCKED.value:
        return process_blocked_event(data)
    elif event == EventsEnum.SOFT_BOUNCE.value:
        return process_softbounce_event(data)
    elif event == EventsEnum.HARD_BOUNCE.value:
        return process_hardbounce_event(data)
    else:
        return {"status": "ignored", "message": "Event not handled"}, 200
