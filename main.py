from flask import Flask, request, jsonify
from config import PORT, ENVIRONMENT
from brevo_service import (
    load_blocked_emails,
    load_softbounce_emails,
    load_hardbounce_emails,
    handle_event
)

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    if ENVIRONMENT not in data.get("tag", []):
        return jsonify({"status": "ignored", "message": "Environment mismatch"}), 200

    result, status = handle_event(data)
    return jsonify(result), status

if __name__ == "__main__":
    load_blocked_emails()      # Initialize the blocked emails list
    load_softbounce_emails()     # Initialize the soft bounce emails list
    load_hardbounce_emails()     # Initialize the hard bounce emails list
    app.run(host="0.0.0.0", port=PORT)
