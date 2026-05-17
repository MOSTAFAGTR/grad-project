import React from 'react';
import { Link } from 'react-router-dom';

const CsrfTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">
        Cross-Site Request Forgery (CSRF) Tutorial
      </h1>

      <p className="text-gray-400 mb-8">
        Learn how attackers trick users into performing unintended actions on trusted websites,
        and how protection mechanisms like CSRF tokens prevent these attacks.
      </p>

      {/* ACTION BUTTONS */}
      <div className="mt-8 flex gap-4">
        {/* Use slug-based routing (consistent with backend) */}
        <Link
          to="/challenges/csrf/attack"
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Try the Attack
        </Link>

        <Link
          to="/challenges/csrf/fix"
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
        >
          Try the Fix
        </Link>
      </div>
    </div>
  );
};

export default CsrfTutorialPage;