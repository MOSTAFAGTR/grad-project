import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  FaLaptopCode, FaWrench, FaGraduationCap, 
  FaShieldAlt, FaVideo, FaClipboardList, FaTrophy 
} from 'react-icons/fa';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleStart = () => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/home'); // Go to Dashboard if logged in
    } else {
      navigate('/login'); // Go to Login if not
    }
  };

  return (
    <div className="bg-gray-900 text-white min-h-screen">
      <div className="container mx-auto px-6 py-16 text-center">
        
        {/* Header Section */}
        <h1 className="text-5xl md:text-7xl font-extrabold text-cyan-400 tracking-wider">
          SCALE
        </h1>
        <p className="text-xl md:text-2xl mt-4 text-gray-300">
          SECURE CODING LEARNING PLATFORM
        </p>
        <p className="text-lg md:text-xl mt-6 text-gray-400 max-w-2xl mx-auto">
          Master secure development by learning real-world vulnerabilities
        </p>
        
        {/* Logic Update: Changed to button with onClick handler, Style kept identical */}
        <button
          onClick={handleStart}
          className="inline-block mt-10 bg-cyan-500 text-white font-bold text-lg py-3 px-8 rounded-full shadow-lg shadow-cyan-500/50 hover:bg-cyan-600 transition-all duration-300 ease-in-out transform hover:scale-105"
        >
          Get Started
        </button>

        {/* How It Works Section */}
        <div className="mt-24">
          <h2 className="text-4xl font-bold mb-12">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-12">
            <div className="flex flex-col items-center">
              <FaLaptopCode className="text-5xl text-blue-400 mb-4" />
              <h3 className="text-2xl font-semibold mb-2">Simulate</h3>
              <p className="text-gray-400">
                Interact with vulnerabilities in a safe environment
              </p>
            </div>
            <div className="flex flex-col items-center">
              <FaWrench className="text-5xl text-green-400 mb-4" />
              <h3 className="text-2xl font-semibold mb-2">Fix</h3>
              <p className="text-gray-400">
                Identify and patch security flaws in your code
              </p>
            </div>
            <div className="flex flex-col items-center">
              <FaGraduationCap className="text-5xl text-purple-400 mb-4" />
              <h3 className="text-2xl font-semibold mb-2">Learn</h3>
              <p className="text-gray-400">
                Understand concepts through tutorials and examples
              </p>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-24">
          <h2 className="text-4xl font-bold mb-12">Features</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="flex flex-col items-center">
              <FaShieldAlt className="text-4xl text-cyan-400 mb-3" />
              <h3 className="text-xl font-semibold">Interactive Challenges</h3>
            </div>
            <div className="flex flex-col items-center">
              <FaVideo className="text-4xl text-green-400 mb-3" />
              <h3 className="text-xl font-semibold">Video Tutorials</h3>
            </div>
            <div className="flex flex-col items-center">
              <FaClipboardList className="text-4xl text-purple-400 mb-3" />
              <h3 className="text-xl font-semibold">Knowledge Quizzes</h3>
            </div>
            <div className="flex flex-col items-center">
              <FaTrophy className="text-4xl text-yellow-400 mb-3" />
              <h3 className="text-xl font-semibold">Leaderboard</h3>
            </div>
          </div>
        </div>
        
        {/* Footer Section */}
        <div className="mt-24 border-t border-gray-800 pt-8">
          <p className="text-2xl font-bold text-gray-300">
            10,000+ <span className="text-gray-400 font-normal">developers trained</span>
          </p>
          <div className="flex justify-between items-center mt-8 text-gray-500">
            <p>© 2024 SCALE</p>
            <Link to="/contact" className="hover:text-white">Contact</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;