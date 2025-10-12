import React from 'react';
import { Link } from 'react-router-dom';

// We now specify the URL for the first challenge
const scenarios = [
  { id: 1, title: 'SQL Injection', url: '/challenges/1/attack' },
  { id: 2, title: 'Cross-Site Scripting', url: '/challenges/2' },
  { id: 3, title: 'Command Injection', url: '/challenges/3' },
  { id: 4, title: 'Broken Authentication', url: '/challenges/4' },
  { id: 5, title: 'Cross-Site Request Forgery', url: '/challenges/5' },
  { id: 6, title: 'Security Misconfiguration', url: '/challenges/6' },
  { id: 7, title: 'Insecure Cryptographic Storage', url: '/challenges/7' },
  { id: 8, title: 'Directory Traversal', url: '/challenges/8' },
  { id: 9, title: 'XML External Entity Injection', url: '/challenges/9' },
  { id: 10, title: 'Unvalidated Redirect', url: '/challenges/10' },
];

const ChallengesListPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold">Select a Scenario</h1>
      <p className="text-gray-400 mt-2 mb-8">Choose an attack/fix scenario to begin</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map((scenario) => (
          // The 'to' prop now uses the URL from our data
          <Link
            key={scenario.id}
            to={scenario.url}
            className="block p-6 bg-gray-900 rounded-lg shadow-md hover:bg-gray-700 transition-colors duration-200"
          >
            <h5 className="mb-2 text-2xl font-bold tracking-tight">
              {scenario.title}
            </h5>
            <p className="font-normal text-gray-400">
              Attack/Fix
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default ChallengesListPage;