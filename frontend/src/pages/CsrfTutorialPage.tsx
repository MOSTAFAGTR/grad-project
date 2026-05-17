import React from 'react';
import { Link } from 'react-router-dom';
import ChallengeTutorialVideo from '../components/ChallengeTutorialVideo';

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

      <ChallengeTutorialVideo challengeId={3} className="mb-2" />

      {/* ACTION BUTTONS */}
      <div className="mt-8 flex gap-4">
        <Link
          to="/challenges/3/attack"
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Try the Attack
        </Link>

        <Link
          to="/challenges/3/fix"
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
        >
          Try the Fix
        </Link>
      </div>
    </div>
  );
};

export default CsrfTutorialPage;