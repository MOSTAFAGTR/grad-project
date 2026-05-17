import React from 'react';
import { Link } from 'react-router-dom';
import ChallengeTutorialVideo from '../components/ChallengeTutorialVideo';

const SqlInjectionTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">SQL Injection Tutorial</h1>
      <p className="text-gray-400 mb-8">This video explains the fundamentals of SQL Injection attacks and how to prevent them.</p>

      <ChallengeTutorialVideo challengeId={1} className="mb-2" />

      <div className="mt-8 flex gap-4">
          <Link to="/challenges/1/attack" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Try the Attack
          </Link>
          <Link to="/challenges/1/fix" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
            Try the Fix
          </Link>
      </div>
    </div>
  );
};

export default SqlInjectionTutorialPage;