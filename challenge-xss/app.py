import os
from flask import Flask, request, jsonify, render_template_string, escape

app = Flask(__name__)

# Very small in-memory store for demonstration only. Tests run in an isolated container
# so this will reset between runs.
messages = []


@app.route('/post', methods=['POST'])
def post_message():
    """API to post a new message. Vulnerable implementations will store user
    supplied content verbatim, and the rendering endpoint (/messages) will reflect it
    without escaping.
    """
    payload = request.json or {}
    message = payload.get('message')

    if not message:
        return jsonify({"error": "Message required"}), 400

    messages.append(message)
    return jsonify({"message": "Posted"}), 200


@app.route('/messages', methods=['GET'])
def show_messages():
    """This endpoint renders the messages in a simple HTML page.
    The vulnerable variant inserts the user-controlled value directly into
    the template (unsafe). The secure variant should escape user input.
    """
    # Build a very small page for demonstration
    content = "<html><body>\n<h1>Messages</h1>\n"

    # NOTE: Insecure: we purposely render the user message directly (vulnerable to XSS).
    # A secure implementation must escape the message using `escape()` or use autoescape.
    for m in messages:
        content += f"<p>{m}</p>\n"

    content += "</body></html>"
    return content, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
