import React from 'react';
import { Link } from 'react-router-dom';

const AttackSuccessPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      {/* The 'animate-pulse' class creates the simple animation */}
      <h1 className="text-4xl font-bold text-green-400 animate-pulse">
        You logged in successfully
      </h1>
      <p className="text-gray-300 mt-4">
        The SQL injection attack was successful!
      </p>
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