import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Allowlist of hosts that are safe to ping (student must enforce this)
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "8.8.8.8"]

@app.route('/ping', methods=['POST'])
def ping():
    """
    Pings the host given in JSON: {"host": "8.8.8.8"}.
    VULNERABILITY: Passes user input to shell (e.g. os.system or subprocess with shell=True).
    Attacker can inject: {"host": "8.8.8.8; id"} or "8.8.8.8 && cat /etc/passwd".
    FIX: Use allowlist (ALLOWED_HOSTS) and run ping via subprocess without shell (list args).
    """
    data = request.get_json() or {}
    host = data.get("host", "").strip()
    if not host:
        return jsonify({"output": "Missing 'host'", "error": True}), 400

    # !!! VULNERABLE: user input passed to shell !!!
    # Student must: validate host in ALLOWED_HOSTS, use subprocess.run(["ping", "-c", "1", host], shell=False)
    try:
        cmd = f"ping -c 1 {host}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = (result.stdout or "") + (result.stderr or "")
        return jsonify({"output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Timeout", "error": True}), 400
    except Exception as e:
        return jsonify({"output": str(e), "error": True}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
