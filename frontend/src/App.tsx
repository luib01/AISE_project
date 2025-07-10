// frontend/src/App.tsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Navbar from "./components/Navbar";
import Dashboard from "./components/Dashboard";
import QuestionAssistant from "./components/QuestionAssistant";
import QuizPage from "./components/QuizPage";
import AdaptiveQuizPage from "./components/AdaptiveQuizPage";
import ChatAssistant from "./components/ChatAssistant";
import SignInPage from "./components/SignInPage";
import SignUpPage from "./components/SignUpPage";
import AccountPage from "./components/AccountPage";
import ProtectedRoute from "./components/ProtectedRoute";
import AdaptiveQuizProtectedRoute from "./components/AdaptiveQuizProtectedRoute";

const HomePage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] bg-gradient-to-b from-indigo-600 to-purple-600 text-white p-4 text-center rounded-lg shadow">
      {isAuthenticated ? (
        <>
          <h1 className="text-4xl font-bold mb-4">
            Welcome back, {user?.username}!
          </h1>
          <p className="max-w-2xl text-lg mb-2">
            Continue your English learning journey with adaptive quizzes and AI Teacher assistance!
          </p>
          <p className="text-sm mb-6 opacity-90">
            Current Level: <span className="font-semibold capitalize">{user?.english_level}</span>
          </p>
          <div className="space-x-4">
            {user?.has_completed_first_quiz ? (
              // Show only adaptive quiz for users who have completed their first quiz
              <a
                href="/adaptive-quiz"
                className="bg-white text-indigo-700 font-semibold px-4 py-2 rounded shadow hover:bg-gray-100 transition duration-200"
              >
                Take Adaptive Quiz
              </a>
            ) : (
              // Show only static quiz for new users
              <a
                href="/quiz"
                className="bg-white text-purple-700 font-semibold px-4 py-2 rounded shadow hover:bg-gray-100 transition duration-200"
              >
                Take Your First Quiz
              </a>
            )}
            <a
              href="/chat"
              className="bg-white text-green-700 font-semibold px-4 py-2 rounded shadow hover:bg-gray-100 transition duration-200"
            >
              AI Teacher
            </a>
            <a
              href="/progress"
              className="bg-white text-blue-700 font-semibold px-4 py-2 rounded shadow hover:bg-gray-100 transition duration-200"
            >
              View Progress
            </a>
          </div>
        </>
      ) : (
        <>
          <h1 className="text-4xl font-bold mb-4">
            Welcome to the English Learning Platform
          </h1>
          <p className="max-w-2xl text-lg mb-6">
            Improve your English with adaptive quizzes, personalized recommendations, and AI Teacher assistance!
          </p>
          <div className="space-x-4">
            <a
              href="/signup"
              className="bg-white text-indigo-700 font-semibold px-6 py-3 rounded shadow hover:bg-gray-100 transition duration-200"
            >
              Get Started - Sign Up
            </a>
            <a
              href="/signin"
              className="bg-transparent border-2 border-white text-white font-semibold px-6 py-3 rounded hover:bg-white hover:text-indigo-700 transition duration-200"
            >
              Sign In
            </a>
          </div>
          <p className="mt-4 text-sm opacity-90">
            Join thousands of learners improving their English skills every day!
          </p>
        </>
      )}
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-gray-100">
          <Navbar />
          <main className="flex-grow container mx-auto p-4">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/signin" element={<SignInPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/adaptive-quiz" element={
                <AdaptiveQuizProtectedRoute>
                  <AdaptiveQuizPage />
                </AdaptiveQuizProtectedRoute>
              } />
              <Route path="/quiz" element={
                <ProtectedRoute>
                  <QuizPage />
                </ProtectedRoute>
              } />
              <Route path="/progress" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/question-assistant" element={
                <ProtectedRoute>
                  <QuestionAssistant />
                </ProtectedRoute>
              } />
              <Route path="/chat" element={
                <ProtectedRoute>
                  <ChatAssistant />
                </ProtectedRoute>
              } />
              <Route path="/account" element={
                <ProtectedRoute>
                  <AccountPage />
                </ProtectedRoute>
              } />
            </Routes>
          </main>
          <footer className="bg-gray-900 text-white text-center py-2">
            &copy; {new Date().getFullYear()} English Learning Platform
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
