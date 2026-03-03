import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from config import PORT, ENVIRONMENT
from brevo_service import handle_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info(f"App initialized with ENVIRONMENT={ENVIRONMENT}")


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "environment": ENVIRONMENT}), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        logger.warning("Received invalid JSON payload")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    event = data.get("event", "unknown")
    email = data.get("email", "unknown")
    tag = data.get("tag", "")

    logger.info(f"Webhook received: event={event}, email={email}, tag={tag}")

    event_date_str = data.get("date", "")
    if event_date_str:
        try:
            event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00")).date()
            today = datetime.now(timezone.utc).date()
            if event_date < today:
                logger.info(f"Skipping: event from {event_date}, before today ({today})")
                return jsonify({"status": "ignored", "message": f"Old event from {event_date}"}), 200
        except (ValueError, TypeError):
            logger.warning(f"Could not parse event date: {event_date_str}")
    else:
        logger.info(f"Skipping: no date field in event for email={email}")
        return jsonify({"status": "ignored", "message": "Missing event date"}), 200

    if ENVIRONMENT not in tag:
        logger.info(f"Skipping: ENVIRONMENT '{ENVIRONMENT}' not in tag '{tag}'")
        return jsonify({"status": "ignored", "message": "Environment mismatch"}), 200

    tags = data.get("tags", [])
    if "skip" in tag or "skip" in tags:
        logger.info(f"Skipping: 'skip' tag found for email={email}")
        return jsonify({"status": "ignored", "message": "Skip tag present"}), 200

    result, status = handle_event(data)
    logger.info(f"Event processed: email={email}, event={event}, status={status}, result={result}")
    return jsonify(result), status

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
