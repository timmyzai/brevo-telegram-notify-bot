from flask import Flask, request, jsonify
from config import PORT, ENVIRONMENT
from brevo_service import handle_event

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


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
    app.run(host="0.0.0.0", port=PORT)
