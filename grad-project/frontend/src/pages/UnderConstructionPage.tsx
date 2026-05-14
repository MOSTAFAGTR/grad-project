import React from 'react';
import { Link } from 'react-router-dom';
import BuildingWallAnimation from '../components/BuildingWallAnimation';

const UnderConstructionPage: React.FC = () => {
  return (
    <div className="bg-gray-800 text-white min-h-screen flex flex-col justify-center items-center text-center p-6">
      
      <BuildingWallAnimation />

      {/* Smaller title for better balance */}
      <h1 className="text-2xl md:text-3xl font-extrabold mt-12 tracking-tight">
        This Page is Under Construction
      </h1>
      <p className="text-base text-gray-400 mt-4 max-w-lg">
        We're working hard to bring this feature online soon.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 mt-10">
        <Link
          to="/challenges"
          className="bg-transparent border-2 border-cyan-400 text-cyan-400 font-bold py-3 px-8 rounded-lg hover:bg-cyan-400 hover:text-gray-900 transition-colors"
        >
          GO BACK TO CHALLENGES
        </Link>
        <a
          href=""
          className="bg-transparent border-2 border-purple-500 text-purple-500 font-bold py-3 px-8 rounded-lg hover:bg-purple-500 hover:text-white transition-colors"
        >
          REPORT AN ISSUE
        </a>
      </div>
    </div>
  );
};

export default UnderConstructionPage;
