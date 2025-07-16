// frontend/src/components/Navbar.tsx
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    setIsDropdownOpen(false);
  };

  return (
    <header className="bg-gray-900 text-white shadow">
      <nav className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="font-bold text-xl">AISE - AI Second-language Educator</div>
        
        <div className="flex items-center space-x-4">
          {/* Navigation Links */}
          <div className="hidden md:flex space-x-4">
            <Link
              to="/"
              className="hover:bg-gray-700 px-3 py-2 rounded transition duration-200"
            >
              Home
            </Link>
            {isAuthenticated && (
              <>
                {user?.has_completed_first_quiz ? (
                  // Show only adaptive quiz for users who completed first quiz
                  <Link
                    to="/adaptive-quiz"
                    className="hover:bg-gray-700 px-3 py-2 rounded transition duration-200"
                  >
                    Adaptive Quiz
                  </Link>
                ) : (
                  // Show only static quiz for new users
                  <Link
                    to="/quiz"
                    className="hover:bg-gray-700 px-3 py-2 rounded transition duration-200"
                  >
                    Take First Quiz
                  </Link>
                )}
                <Link
                  to="/progress"
                  className="hover:bg-gray-700 px-3 py-2 rounded transition duration-200"
                >
                  Progress
                </Link>
                <Link
                  to="/chat"
                  className="hover:bg-gray-700 px-3 py-2 rounded transition duration-200"
                >
                  AI Teacher
                </Link>
              </>
            )}
          </div>

          {/* Authentication Section */}
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center space-x-2 hover:bg-gray-700 px-3 py-2 rounded transition duration-200"
              >
                <span>Welcome, {user?.username}</span>
                <svg
                  className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                  <div className="px-4 py-2 text-sm text-gray-700 border-b">
                    <div className="font-medium">{user?.username}</div>
                    <div className="text-xs text-gray-500 capitalize">{user?.english_level} Level</div>
                  </div>
                  <Link
                    to="/account"
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    onClick={() => setIsDropdownOpen(false)}
                  >
                    Account Settings
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex space-x-2">
              <Link
                to="/signin"
                className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded transition duration-200"
              >
                Sign In
              </Link>
              <Link
                to="/signup"
                className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition duration-200"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
