import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import axios from "axios";

//The Fix:
/*
from flask import Flask, request, jsonify
from markupsafe import escape

app = Flask(__name__)

messages = []

@app.route('/post', methods=['POST'])
def post_message():
    payload = request.get_json(silent=True) or {}
    message = payload.get('message')
    if not message or not isinstance(message, str):
        return jsonify({"error": "Message (string) required"}), 400

    messages.append(message)
    return jsonify({"message": "Posted"}), 200

@app.route('/messages', methods=['GET'])
def show_messages():
    html = '''<html><body>
<h1>Messages</h1>
'''
    for m in messages:
        html += f"<p>{escape(m)}</p>"

    html += '</body></html>'
    return html, 200

if __name__ == '__main__':
    app.run(debug=True)
*/

const VULNERABLE_CODE = `from flask import Flask, request, jsonify

app = Flask(__name__)

messages = []

@app.route('/post', methods=['POST'])
def post_message():
    payload = request.json or {}
    message = payload.get('message')
    if not message:
        return jsonify({"error": "Message required"}), 400
    
    messages.append(message)
    return jsonify({"message": "Posted"}), 200

@app.route('/messages', methods=['GET'])
def show_messages():
    html = '''<html><body>
<h1>Messages</h1>
'''
    for m in messages:
        html += f"<p>{m}</p>" 
        
    html += '</body></html>'
    return html, 200

if __name__ == '__main__':
    app.run(debug=True)
`;

const XssFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [feedback, setFeedback] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    setIsLoading(true);
    setFeedback("");
    try {
      const { data } = await axios.post(
        "http://localhost:8000/api/challenges/submit-fix",
        { code, challenge: "xss" }
      );
      setIsSuccess(data.success);
      setFeedback(data.logs);
      if (data.success) {
        alert(
          "Congratulations! Your fix is correct and passed all security tests."
        );
      } else {
        alert("Your fix is not correct. Check the logs for details.");
      }
    } catch (err: any) {
      setFeedback(err.message || "Error");
      alert("An error occurred while submitting your code.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">XSS: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">
        The page below is vulnerable to XSS. Update rendering to escape user
        input using MarkupSafe's escape or similar.
      </p>

      <div className="h-96 mb-4 border-2 border-gray-700 rounded-lg overflow-hidden">
        <Editor
          height="100%"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(v) => setCode(v || "")}
        />
      </div>

      <button
        onClick={handleSubmit}
        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded"
        disabled={isLoading}
      >
        {isLoading ? "Running Tests..." : "Submit Fix"}
      </button>

      {feedback && (
        <div
          className={`mt-6 p-4 rounded-lg text-sm ${
            isSuccess
              ? "bg-green-900 text-green-200"
              : "bg-red-900 text-red-200"
          }`}
        >
          <pre className="whitespace-pre-wrap">{feedback}</pre>
        </div>
      )}
    </div>
  );
};

export default XssFixPage;
