import React from 'react';
import { Link } from 'react-router-dom';
import { useLocation } from 'react-router-dom';

const AttackSuccessPage: React.FC = () => {
  const q = new URLSearchParams(useLocation().search);
  const type = q.get("type") || "sql";

  return (
    <div className="bg-gray-800 text-white min-h-screen flex flex-col justify-center items-center text-center p-6">
      {/* Skull SVG Icon */}
      <div className="mb-8">
        <p className='text-9xl
'>☠️</p>
      </div>

      {/* Title */}
      <h1 className="text-4xl md:text-5xl font-extrabold mt-4 tracking-tight text-red-500">
        ATTACK SUCCESSFUL!
      </h1>
      <p className="text-lg text-gray-300 mt-4 max-w-lg">
        You've successfully exploited the vulnerability. This demonstrates the danger of insecure code.
      </p>

      {/* Navigation Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 mt-10">
        <Link
          to="/challenges"
          className="bg-transparent border-2 border-cyan-400 text-cyan-400 font-bold py-3 px-8 rounded-lg hover:bg-cyan-400 hover:text-gray-900 transition-colors"
        >
          BACK TO CHALLENGES
        </Link>
        <Link
          to="/dashboard"
          className="bg-transparent border-2 border-purple-500 text-purple-500 font-bold py-3 px-8 rounded-lg hover:bg-purple-500 hover:text-white transition-colors"
        >
          GO TO DASHBOARD
        </Link>
      </div>
    </div>
  );
};

export default AttackSuccessPage;
