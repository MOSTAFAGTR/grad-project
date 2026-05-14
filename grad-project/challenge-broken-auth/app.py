from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Mock Database
users = {
    "admin": "complex_password_123"
}

# TODO: Implement a storage for failed attempts
# failed_attempts = {}

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    # !!! VULNERABILITY !!!
    # There is no check here for how many times the user failed.
    # An attacker can try 1000 passwords per second.
    
    # --- FIX INSTRUCTIONS ---
    # 1. Check if user is currently locked out.
    # 2. If password is wrong, increment failure count.
    # 3. If failure count > 3, block requests for a few seconds.

    if username in users and users[username] == password:
        # Reset counter on success
        return jsonify({"message": "Login successful", "token": "xyz123"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)