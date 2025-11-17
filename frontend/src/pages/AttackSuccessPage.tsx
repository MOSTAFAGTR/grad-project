import React from "react";
import { Link } from "react-router-dom";
import { useLocation } from "react-router-dom";

const AttackSuccessPage: React.FC = () => {
  const q = new URLSearchParams(useLocation().search);
  const type = q.get("type") || "sql";

  const title =
    type === "xss" ? "XSS Attack Successful" : "You logged in successfully";
  const message =
    type === "xss"
      ? "The application reflected raw user input, allowing script execution."
      : "The SQL injection attack was successful!";

  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      {/* The 'animate-pulse' class creates the simple animation */}
      <h1 className="text-4xl font-bold text-green-400 animate-pulse">
        {title}
      </h1>
      <p className="text-gray-300 mt-4">{message}</p>
      <Link
        to="/challenges"
        className="mt-8 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        Return to Challenges
      </Link>
    </div>
  );
};

export default AttackSuccessPage;
