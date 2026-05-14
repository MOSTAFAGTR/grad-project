from flask import Flask, request, jsonify
import os
import traceback

app = Flask(__name__)

# !!! VULNERABILITY 1: DEBUG MODE ENABLED !!!
app.config['DEBUG'] = True
app.config['ENV'] = 'development'

# !!! VULNERABILITY 2: HARDCODED SECRETS !!!
SECRET_KEY = "SUPER_SECRET_KEY_123"
DB_PASSWORD = "DB_PASS_456"

# !!! VULNERABILITY 3: DEFAULT CREDENTIALS !!!
ADMIN_USER = "admin"
ADMIN_PASS = "admin"


@app.route('/login', methods=['POST'])
def login():
    u = request.json.get('username')
    p = request.json.get('password')

    if u == ADMIN_USER and p == ADMIN_PASS:
        return jsonify({
            "message": "Welcome Admin",
            "secret_key": SECRET_KEY,   # ❌ leaking secret
            "db_password": DB_PASSWORD # ❌ leaking secret
        }), 200

    return jsonify({"error": "Bad creds"}), 401


@app.route('/leak-env')
def leak_env():
    # ❌ Exposes environment variables
    return jsonify(dict(os.environ))


@app.route('/crash')
def trigger_error():
    # ❌ Stack trace + secrets leak
    try:
        1 / 0
    except:
        return jsonify({
            "error": "Application crashed",
            "trace": traceback.format_exc(),
            "config": {
                "SECRET_KEY": SECRET_KEY,
                "DB_PASSWORD": DB_PASSWORD,
                "DEBUG": app.config['DEBUG'],
                "ENV": app.config['ENV']
            }
        })


if __name__ == '__main__':
    # ❌ NEVER DO THIS IN PRODUCTION
    app.run(host='0.0.0.0', port=5000, debug=True)
