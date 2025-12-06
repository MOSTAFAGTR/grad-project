from flask import Flask, request, render_template_string

app = Flask(__name__)

# Mock database for the sandbox environment
comments = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content', '')
        # In a real scenario, we'd save this to a DB
        comments.append(content)

    # !!! VULNERABLE CODE !!!
    # The application takes user input (comments) and concatenates it 
    # directly into the HTML string without sanitization (escaping).
    # An attacker can input "<script>alert('XSS')</script>" and it will execute.
    
    comments_html = ""
    for c in comments:
        comments_html += f"<div class='comment'>{c}</div>"

    template = f"""
    <!doctype html>
    <html>
    <body>
        <h1>Blog Comments</h1>
        <form method="post">
            <input type="text" name="content" placeholder="Add a comment">
            <button type="submit">Post</button>
        </form>
        <div id="comments-section">
            {comments_html}
        </div>
    </body>
    </html>
    """
    
    return render_template_string(template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
