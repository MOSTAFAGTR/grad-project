from flask import Flask, request, redirect, abort
from urllib.parse import urlparse

app = Flask(__name__)

# Allowed relative paths (student must restrict redirects to this allowlist)
ALLOWED_PATHS = ['/dashboard', '/profile', '/settings', '/home']


@app.route('/go')
def go():
    """
    Secure redirect endpoint.
    - Only allows relative paths from ALLOWED_PATHS.
    - Rejects absolute URLs (e.g. https://evil.com).
    - Rejects protocol-relative URLs (e.g. //evil.com).
    """
    target = request.args.get('next') or request.args.get('url') or '/'

    parsed = urlparse(target)

    # Block absolute and protocol-relative URLs
    if parsed.scheme or parsed.netloc:
        abort(400)

    # Require a leading slash for local paths
    if not target.startswith('/'):
        abort(400)

    # Enforce allowlist
    if target not in ALLOWED_PATHS:
        abort(400)

    return redirect(target, code=302)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
