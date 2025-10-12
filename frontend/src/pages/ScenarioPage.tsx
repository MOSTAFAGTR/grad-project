import React from 'react';
import { useParams, Link } from 'react-router-dom';

const ScenarioPage: React.FC = () => {
  // This hook gets the 'id' from the URL (e.g., /challenges/5)
  const { id } = useParams<{ id: string }>();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to Scenario {id}</h1>
        <p className="text-lg text-gray-600 mb-8">
          The challenge content for this scenario will be displayed here.
        </p>
        <Link
          to="/challenges"
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Back to Scenarios List
        </Link>
      </div>
    </div>
  );
};

export default ScenarioPage;
