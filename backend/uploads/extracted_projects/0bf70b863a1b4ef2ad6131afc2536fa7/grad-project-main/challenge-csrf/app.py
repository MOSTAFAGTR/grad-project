import sqlite3
from flask import Flask, request, jsonify, session
import secrets

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_testing'

# --- Database Setup (SQLite for Sandbox) ---
def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE accounts (username TEXT, balance INT)')
    c.execute("INSERT INTO accounts VALUES ('Alice', 1000)")
    c.execute("INSERT INTO accounts VALUES ('Bob', 0)")
    conn.commit()
    return conn

# We keep the connection open for this simple single-threaded test script
db_conn = init_db()

@app.route('/transfer', methods=['POST'])
def transfer():
    """
    Handles money transfer.
    VULNERABILITY: 
    This endpoint relies ONLY on the session cookie.
    It does not check for a CSRF token in the request body/headers.
    """
    
    # Simulate logged-in user
    current_user = 'Alice'
    
    to_user = request.form.get('to_user')
    amount = request.form.get('amount')
    
    if not to_user or not amount:
        return jsonify({"error": "Missing parameters"}), 400
        
    try:
        amount = int(amount)
    except:
        return jsonify({"error": "Invalid amount"}), 400

    # !!! FIX NEEDED HERE !!!
    # Student must add:
    # 1. Get token from session
    # 2. Get token from request
    # 3. Compare them. If mismatch -> return 403
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE username=?", (current_user,))
    row = cursor.fetchone()
    
    if row and row[0] >= amount:
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE username=?", (amount, current_user))
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE username=?", (amount, to_user))
        db_conn.commit()
        return jsonify({"message": "Transfer successful"}), 200
    else:
        return jsonify({"error": "Insufficient funds"}), 400

@app.route('/form', methods=['GET'])
def transfer_form():
    # Student must implement token generation here
    # token = secrets.token_hex(16)
    # session['csrf_token'] = token
    # return jsonify(..., "csrf_token": token)
    return jsonify({"message": "Form loaded", "csrf_token": "TODO_IMPLEMENT_ME"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)