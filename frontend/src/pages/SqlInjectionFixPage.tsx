import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import axios from "axios";

const VULNERABLE_CODE = `import os
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="challenge_db_sqli", # Connect to the dedicated challenge DB
        user="user",
        password="password",
        database="testdb"
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # !!! VULNERABLE CODE !!!
    # Fix this query to prevent SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    try:
        cursor.execute(query)
        user = cursor.fetchone()

        if user:
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
`;


const SqlInjectionFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [feedback, setFeedback] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  const handleSubmit = async () => {
    setIsLoading(true);
    setFeedback("");
    try {
      const response = await axios.post(
        "http://localhost:8000/api/challenges/submit-fix",
        { code, challenge: "sql-injection" }
      );
      const { success, logs } = response.data;

      setIsSuccess(success);
      setFeedback(logs);

      if (success) {
        alert(
          "Congratulations! Your fix is correct and passed all security tests."
        );
      } else {
        alert("Your fix is not correct. Check the logs for details.");
      }
    } catch (error) {
      console.error(error);
      setFeedback("An error occurred while submitting your code.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">SQL Injection: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">
        The code below is vulnerable to SQL Injection. Modify the query to use
        parameterized statements (query parameters) to prevent the
        vulnerability. Your solution must still allow a valid user ('admin' with
        password 'password123') to log in.
      </p>

      <div className="h-96 mb-4 border-2 border-gray-700 rounded-lg overflow-hidden">
        <Editor
          height="100%"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value || "")}
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
                ? "Your fix successfully prevents SQL injection attacks."
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

export default SqlInjectionFixPage;
