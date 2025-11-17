import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

// The exploit: <script>alert('XSS')</script>;

const XssAttackPage: React.FC = () => {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setResult("");
    try {
      const response = await axios.post(
        "http://localhost:8000/api/challenges/vulnerable-xss",
        { message }
      );
      const html = response.data?.html || "";

      // If the returned HTML contains a raw <script> payload it's a simulation of XSS succeeding
      if (html.includes("<script")) {
        navigate("/challenges/attack-success?type=xss");
      } else {
        setResult("No XSS reflected (browser escaped content).");
      }
    } catch (err: any) {
      setResult(err.message || "Error");
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">XSS Simulation</h1>
      <p className="text-gray-400 mb-6">
        Enter a message to send to the application. An attacker could include a
        script tag to perform an XSS attack.
      </p>

      <div className="w-full max-w-sm p-6 bg-gray-900 rounded-lg border border-gray-700">
        <div className="mb-4">
          <label className="block text-gray-300 text-sm font-bold mb-2">
            Message
          </label>
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5"
          />
        </div>
        <div className="flex justify-end">
          <button
            onClick={handleSubmit}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Send
          </button>
        </div>
      </div>

      {result && <div className="mt-4 text-red-400">{result}</div>}
    </div>
  );
};

export default XssAttackPage;
