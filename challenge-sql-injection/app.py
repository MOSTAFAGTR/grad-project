import os
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Database Connection ---
def get_db_connection():
    """Connects to the MySQL database."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"), # 'db' is the name of our mysql service in docker-compose
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "password"),
        database=os.environ.get("DB_NAME", "testdb")
    )

# --- Routes ---
@app.route('/login', methods=['POST'])
def login():
    """
    Handles user login.
    This function contains a SQL injection vulnerability.
    """
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # !!! VULNERABLE CODE !!!
    # The query is built by concatenating user-provided strings directly.
    # An attacker can manipulate the username to change the query's logic.
    # For example, a username of "admin' OR '1'='1" would bypass the password check.
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    try:
        cursor.execute(query)
        user = cursor.fetchone()

        if user:
            # In a real app, you'd return a session token. Here, we just confirm success.
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# This allows the app to be run directly for testing if needed
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)