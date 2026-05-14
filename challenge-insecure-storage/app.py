import hashlib
from flask import Flask, jsonify, request

app = Flask(__name__)
USERS = {}


@app.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        return jsonify({"error": "username/password required"}), 400

    # Vulnerable by default: stores plaintext password.
    USERS[username] = {"password": password}
    return jsonify({"ok": True, "username": username}), 200


@app.route("/dump")
def dump_users():
    return jsonify({"users": USERS}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
