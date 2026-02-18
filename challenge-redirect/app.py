from flask import Flask, request, redirect

app = Flask(__name__)

# Allowed relative paths (student must restrict redirects to this allowlist)
ALLOWED_PATHS = ['/dashboard', '/profile', '/settings', '/home']

@app.route('/go')
def go():
    """
    Redirects the user based on 'next' or 'url' query parameter.
    VULNERABILITY: No validation - any URL is accepted (open redirect).
    FIX: Validate the target URL against an allowlist (e.g. same-origin relative paths only).
    """
    target = request.args.get('next') or request.args.get('url') or '/'
    # !!! VULNERABLE: redirecting to user-controlled URL without validation !!!
    # Student must: parse target, allow only relative paths in ALLOWED_PATHS, else return 400
    return redirect(target, code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
