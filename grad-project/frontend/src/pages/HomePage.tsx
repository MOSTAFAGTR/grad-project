import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="container mx-auto px-4">
      <h1 className="text-4xl font-bold text-center my-8">Welcome to SCALE</h1>
      <p className="text-lg text-center mb-8">
        Your interactive environment for learning secure coding principles.
      </p>
      <div className="flex justify-center space-x-4">
        <Link to="/login" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Login
        </Link>
        <Link to="/register" className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
          Register
        </Link>
      </div>
    </div>
  );
};

export default HomePage;