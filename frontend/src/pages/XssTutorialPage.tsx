import React from 'react';
import { Link } from 'react-router-dom';
import ChallengeTutorialVideo from '../components/ChallengeTutorialVideo';

const XssTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">Cross-Site Scripting (XSS) Tutorial</h1>
      <p className="text-gray-400 mb-8">Learn how attackers inject malicious scripts into trusted websites and how to prevent it.</p>

      <ChallengeTutorialVideo challengeId={2} className="mb-2" />

      <div className="mt-8 flex gap-4">
          <Link to="/challenges/2/attack" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Try the Attack
          </Link>
          <Link to="/challenges/2/fix" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
            Try the Fix
          </Link>
      </div>
    </div>
  );
};

export default XssTutorialPage;