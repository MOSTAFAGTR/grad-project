import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Allowlist of hosts that are safe to ping (student must enforce this)
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "8.8.8.8"]

@app.route('/ping', methods=['POST'])
def ping():

    data = request.get_json() or {}
    host = data.get("host", "").strip()
    if not host:
        return jsonify({"output": "Missing 'host'", "error": True}), 400

    if host not in ALLOWED_HOSTS:
        return jsonify({
            "output": f"Host not allowed. Allowed hosts: {', '.join(ALLOWED_HOSTS)}",
            "error": True,
        }), 403

    try:
        result = subprocess.run(
            ["ping", "-c", "1", host],
            shell=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return jsonify({"output": output})
    except FileNotFoundError:
        # Keep the training app usable in minimal runtimes where ping is unavailable.
        return jsonify({"output": f"[simulated] ping unavailable for host: {host}"})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Timeout", "error": True}), 400
    except Exception as e:
        return jsonify({"output": str(e), "error": True}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
