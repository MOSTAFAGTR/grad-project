import React from 'react';
import { Link } from 'react-router-dom';

const SqlInjectionTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">SQL Injection Tutorial</h1>
      <p className="text-gray-400 mb-8">This video explains the fundamentals of SQL Injection attacks and how to prevent them.</p>

      {/* NATIVE HTML5 VIDEO PLAYER */}
      <div className="w-full max-w-4xl mx-auto rounded-lg overflow-hidden border-2 border-gray-700">
        <video
          className="w-full h-full"
          controls // This enables play, pause, volume, fullscreen, etc.
          // The src path is a direct path from the public folder
          src="/WhatsApp Video 2025-11-12 at 19.31.45_ab683d15.mp4" 
        >
          Your browser does not support the video tag.
        </video>
      </div>

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