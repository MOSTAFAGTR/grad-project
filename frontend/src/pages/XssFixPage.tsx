import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';

const VULNERABLE_CODE = `from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Mock storage
    comments = [] 
    if request.method == 'POST':
        # We are getting the content directly from the form
        content = request.form.get('content', '')
        comments.append(content)

    # Building HTML manually (VULNERABLE)
    comments_html = ""
    for c in comments:
        comments_html += f"<div class='comment'>{c}</div>"

    template = f"""
    <!doctype html>
    <html>
    <body>
        <h1>Comments</h1>
        <form method="post">
            <input type="text" name="content">
            <button type="submit">Post</button>
        </form>
        <div>
            {comments_html}
        </div>
    </body>
    </html>
    """
    
    # HINT: Use html.escape(c) or render_template with autoescaping
    # If using raw string building, you must import 'html' and use html.escape()
    
    return render_template_string(template)
`;


const XssFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [feedback, setFeedback] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  const handleSubmit = async () => {
    setIsLoading(true);
    setFeedback('');
    try {
      // Note: Calling the new specific XSS endpoint
      const response = await axios.post('http://localhost:8000/api/challenges/submit-fix-xss', { code });
      const { success, logs } = response.data;

      setIsSuccess(success);
      setFeedback(logs);

      if (success) {
        alert("Congratulations! You successfully sanitized the input.");
      } else {
        alert("Vulnerability still exists or code error. Check logs.");
      }

    } catch (error) {
      console.error(error);
      setFeedback('An error occurred while submitting your code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">XSS: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">
        The code below constructs HTML using strings, allowing attackers to inject scripts.
        Fix it by importing `html` and using `html.escape(content)` before adding it to the HTML string.
      </p>

      <div className="h-96 mb-4 border-2 border-gray-700 rounded-lg overflow-hidden">
        <Editor
          height="100%"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value || '')}
        />
      </div>

      <button
        onClick={handleSubmit}
        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded"
        disabled={isLoading}
      >
        {isLoading ? 'Running Tests...' : 'Submit Fix'}
      </button>

      {feedback && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">Test Results:</h3>
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded text-sm"
            >
              {showLogs ? "Hide Logs" : "Show Logs"}
            </button>
          </div>

          <div
            className={`p-4 rounded-lg mb-4 ${isSuccess
              ? "bg-green-900 text-green-200"
              : "bg-red-900 text-red-200"
              }`}
          >
            <div className="text-lg font-bold mb-2">
              {isSuccess ? "✓ Code is Fixed!" : "✗ Code is Still Vulnerable"}
            </div>
            <div className="text-sm">
              {isSuccess
                ? "Your fix successfully prevents XSS attacks."
                : "The vulnerability still exists. Review the logs for details."}
            </div>
          </div>

          {showLogs && (
            <pre className="bg-gray-900 p-4 rounded-lg text-sm whitespace-pre-wrap border border-gray-700">
              {feedback}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};

export default XssFixPage;
