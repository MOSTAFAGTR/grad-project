import React from 'react';
import { FaCheckCircle, FaTimesCircle, FaChevronDown, FaBug } from 'react-icons/fa';

interface ResultModalProps {
  isOpen: boolean;
  isSuccess: boolean;
  logs: string;
  onClose: () => void;
}

const ResultModal: React.FC<ResultModalProps> = ({ isOpen, isSuccess, logs, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm transition-opacity duration-300">
      <div className={`bg-gray-800 rounded-xl shadow-2xl p-8 max-w-lg w-full mx-4 border-2 transform transition-all duration-300 scale-100 ${isSuccess ? 'border-green-500' : 'border-red-500'}`}>
        
        {/* 1. Animated Icon & One-Line Status */}
        <div className="flex flex-col items-center mb-6">
          {isSuccess ? (
            <FaCheckCircle className="text-7xl text-green-500 mb-4 animate-bounce" />
          ) : (
            <FaTimesCircle className="text-7xl text-red-500 mb-4 animate-pulse" />
          )}
          
          <h2 className={`text-3xl font-extrabold ${isSuccess ? 'text-green-400' : 'text-red-400'}`}>
            {isSuccess ? 'CHALLENGE SOLVED!' : 'FIX FAILED'}
          </h2>
          
          <p className="text-gray-300 mt-2 text-center text-lg font-medium">
            {isSuccess 
              ? "Great job! Your code passed all security tests." 
              : "Your solution did not fix the vulnerability."}
          </p>
        </div>

        {/* 2. Dropdown for Logs */}
        <div className="bg-gray-900/80 rounded-lg overflow-hidden border border-gray-700 mb-6">
          <details className="group">
            <summary className="cursor-pointer p-3 font-semibold text-blue-400 hover:text-blue-300 hover:bg-gray-800 flex justify-between items-center transition select-none">
              <span className="flex items-center gap-2">
                <FaBug /> View Execution Logs
              </span>
              <FaChevronDown className="text-xs transition-transform group-open:rotate-180" />
            </summary>
            
            {/* The Logs Content */}
            <div className="p-4 border-t border-gray-700 bg-black/50">
              <pre className={`text-xs whitespace-pre-wrap font-mono max-h-48 overflow-y-auto ${isSuccess ? 'text-green-400' : 'text-red-300'}`}>
                {logs || "No output logs returned from sandbox."}
              </pre>
            </div>
          </details>
        </div>

        {/* 3. Action Button */}
        <button 
          onClick={onClose}
          className={`w-full py-3 rounded-lg font-bold text-white text-lg transition transform hover:scale-105 shadow-lg ${isSuccess ? 'bg-green-600 hover:bg-green-700 shadow-green-900/50' : 'bg-red-600 hover:bg-red-700 shadow-red-900/50'}`}
        >
          {isSuccess ? 'Continue' : 'Try Again'}
        </button>
      </div>
    </div>
  );
};

export default ResultModal;