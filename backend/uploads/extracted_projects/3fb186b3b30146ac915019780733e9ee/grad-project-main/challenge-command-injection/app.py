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

    # ============================================================================================
    # ⚠️  VULNERABILITY: COMMAND INJECTION ⚠️
    # ============================================================================================
    # 
    # THE PROBLEM:
    # ------------
    # The current code uses shell=True, which means the command is executed through a shell
    # (like bash). This allows attackers to inject additional commands using shell metacharacters.
    #
    # Example attack:
    #   Attacker sends: {"host": "8.8.8.8; id"}
    #   The shell interprets this as TWO commands:
    #     1. ping -c 1 8.8.8.8
    #     2. id  ← This extra command executes!
    #
    # Other dangerous characters that can be injected:
    #   - ;  (semicolon - runs next command)
    #   - && (runs next command if previous succeeds)
    #   - || (runs next command if previous fails)
    #   - |  (pipe - sends output to next command)
    #   - `  (backticks - command substitution)
    #   - $() (command substitution)
    #
    # THE FIX (TWO PARTS REQUIRED):
    # ------------------------------
    #
    # PART 1: INPUT VALIDATION (ALLOWLIST)
    #   Before running ANY command, validate that the host is in ALLOWED_HOSTS.
    #   This prevents attackers from using ANY host, even if they bypass other protections.
    #
    #   Add this BEFORE the try block:
    #   ```
    #   if host not in ALLOWED_HOSTS:
    #       return jsonify({"error": "Host not allowed", "output": f"Only these hosts are allowed: {ALLOWED_HOSTS}"}), 403
    #   ```
    #
    # PART 2: USE shell=False (NO SHELL INTERPRETATION)
    #   Instead of passing a string to shell=True, pass a LIST of arguments to shell=False.
    #   This runs the command directly without shell interpretation, so metacharacters
    #   are treated as literal characters, not commands.
    #
    #   Replace the vulnerable code:
    #   ```
    #   cmd = f"ping -c 1 {host}"  # ❌ String interpolation - dangerous!
    #   result = subprocess.run(cmd, shell=True, ...)  # ❌ shell=True - dangerous!
    #   ```
    #
    #   With the secure version:
    #   ```
    #   result = subprocess.run(["ping", "-c", "1", host], shell=False, capture_output=True, text=True, timeout=5)
    #   ```
    #
    # WHY THIS WORKS:
    # --------------
    # 1. Input validation blocks unauthorized hosts BEFORE any command runs.
    # 2. shell=False means:
    #    - The command and arguments are passed as a list directly to the OS
    #    - No shell interprets special characters
    #    - Even if host = "8.8.8.8; id", it tries to ping a host literally named "8.8.8.8; id"
    #    - The "id" part is never executed as a separate command
    #
    # EXAMPLE OF SECURE CODE:
    # -----------------------
    # if host not in ALLOWED_HOSTS:
    #     return jsonify({"error": "Host not allowed"}, 403)
    # 
    # result = subprocess.run(["ping", "-c", "1", host], shell=False, capture_output=True, text=True, timeout=5)
    #
    # ============================================================================================
    
    try:
        cmd = f"ping -c 1 {host}"  # ❌ VULNERABLE: String interpolation allows injection
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)  # ❌ VULNERABLE: shell=True interprets metacharacters
        output = (result.stdout or "") + (result.stderr or "")
        return jsonify({"output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Timeout", "error": True}), 400
    except Exception as e:
        return jsonify({"output": str(e), "error": True}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
