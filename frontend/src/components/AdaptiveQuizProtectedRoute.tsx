// frontend/src/components/AdaptiveQuizProtectedRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface AdaptiveQuizProtectedRouteProps {
  children: React.ReactNode;
}

const AdaptiveQuizProtectedRoute: React.FC<AdaptiveQuizProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[50vh]">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }

  // Redirect to static quiz if user hasn't completed their first quiz
  if (!user?.has_completed_first_quiz) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h2 className="text-xl font-semibold text-yellow-800 mb-4">
          Complete Your First Quiz
        </h2>
        <p className="text-yellow-700 mb-4">
          You need to complete your first static quiz before accessing adaptive quizzes. 
          This helps us understand your current English level and provide personalized questions.
        </p>
        <a
          href="/quiz"
          className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700 transition duration-200"
        >
          Take Your First Quiz
        </a>
      </div>
    );
  }

  return <>{children}</>;
};

export default AdaptiveQuizProtectedRoute;
