// frontend/src/components/AdaptiveQuizPage.tsx
import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import apiClient from "../api/apiClient";
import { 
  ADAPTIVE_QUIZ_ENDPOINT, 
  QUIZ_EVALUATION_ENDPOINT, 
  USER_PROFILE_ENDPOINT,
  QUIZ_TOPICS_ENDPOINT 
} from "../api/endpoints";

interface Question {
  passage?: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  topic: string;
  difficulty: string;
}

interface UserProfile {
  user_id: string;
  english_level: string;
  progress: Record<string, number>;
  total_quizzes: number;
  average_score: number;
  level_changed?: boolean;
  previous_level?: string;
  level_change_type?: string;
  level_change_message?: string;
}

interface Topic {
  name: string;
  subtopics: string[];
  levels: string[];
}

const AdaptiveQuizPage: React.FC = () => {
  const { user } = useAuth();
  const [selectedTopic, setSelectedTopic] = useState("Mixed");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [quizResult, setQuizResult] = useState<any>(null);
  const [detailedResults, setDetailedResults] = useState<any[]>([]);

  useEffect(() => {
    if (user) {
      loadUserProfile();
      loadTopics();
    }
  }, [user]);

  const loadUserProfile = async () => {
    if (!user) return;
    try {
      const response = await apiClient.get(`${USER_PROFILE_ENDPOINT}${user.user_id}`);
      setUserProfile(response.data);
    } catch (err) {
      console.error("Error loading user profile:", err);
    }
  };

  const loadTopics = async () => {
    try {
      const response = await apiClient.get(QUIZ_TOPICS_ENDPOINT);
      setTopics(response.data.topics || []);
    } catch (err) {
      console.error("Error loading topics:", err);
    }
  };

  const generateAdaptiveQuiz = async () => {
    if (!user) {
      setError("User not authenticated");
      return;
    }

    setLoading(true);
    setError("");
    setQuestions([]);
    setAnswers({});
    setSubmitted(false);

    try {
      const response = await apiClient.post(ADAPTIVE_QUIZ_ENDPOINT, {
        topic: selectedTopic,
        num_questions: 4
      });

      if (response.data.questions) {
        setQuestions(response.data.questions);
        setError("");
      } else {
        setError("Failed to generate quiz. Please try again.");
      }
    } catch (err) {
      console.error("Error generating quiz:", err);
      setError("Error generating adaptive quiz. Please check if Ollama is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionIndex: number, choice: string) => {
    setAnswers({ ...answers, [questionIndex]: choice });
  };

  const handleSubmitQuiz = async () => {
    if (questions.length === 0) return;

    let totalCorrect = 0;
    const quizData = questions.map((q, index) => {
      const userAnswer = answers[index] || "";
      const isCorrect = userAnswer === q.correct_answer;
      if (isCorrect) totalCorrect++;
      return {
        question: q.question,
        topic: q.topic,
        userAnswer,
        correctAnswer: q.correct_answer,
        isCorrect,
        explanation: q.explanation,
        difficulty: q.difficulty
      };
    });

    const score = Math.round((totalCorrect / questions.length) * 100);

    // Store detailed results for display
    setDetailedResults(quizData);

    try {
      const response = await apiClient.post(QUIZ_EVALUATION_ENDPOINT, {
        quiz_data: { questions: quizData },
        score,
        topic: selectedTopic,
        difficulty: userProfile?.english_level || "beginner",
        quiz_type: "adaptive"
      });

      setQuizResult(response.data);
      setSubmitted(true);

      // Reload user profile to get updated level
      await loadUserProfile();

      // Show success message
      let message = `Quiz completed! Score: ${score}%`;
      if (response.data.level_changed) {
        message += `\n🎉 ${response.data.level_change_message}`;
      }
      alert(message);
    } catch (err) {
      console.error("Error submitting quiz:", err);
      alert("Failed to submit quiz!");
    }
  };

  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case "beginner": return "bg-green-100 text-green-800";
      case "intermediate": return "bg-yellow-100 text-yellow-800";
      case "advanced": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow text-gray-800 max-w-4xl mx-auto">
      <h2 className="text-2xl font-semibold mb-6">AISE Adaptive Quiz</h2>
      
      {/* User Profile Section */}
      {userProfile && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">Your Learning Profile</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-gray-600">Level:</span>
              <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${getLevelBadgeColor(userProfile.english_level)}`}>
                {userProfile.english_level.toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Total Quizzes:</span>
              <span className="ml-2 font-medium">{userProfile.total_quizzes}</span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Average Score:</span>
              <span className="ml-2 font-medium">{userProfile.average_score.toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Progress:</span>
              <span className="ml-2 font-medium">
                {Object.keys(userProfile.progress).length} topics
              </span>
            </div>
          </div>
          {userProfile.level_changed && (
            <div className={`mt-2 p-2 rounded text-sm ${
              userProfile.level_change_type === 'retrocession' 
                ? 'bg-red-100 text-red-800' 
                : 'bg-green-100 text-green-800'
            }`}>
              {userProfile.level_change_type === 'retrocession' 
                ? '📉 Recently changed from' 
                : '🎉 Recently progressed from'
              } {userProfile.previous_level} to {userProfile.english_level}!
            </div>
          )}
        </div>
      )}

      {!submitted && (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4">
            <div>
              <label htmlFor="topic" className="block font-medium mb-1">
                Topic:
              </label>
              <select
                id="topic"
                className="border border-gray-300 rounded px-3 py-2 w-full"
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
              >
                {topics.map((topic) => (
                  <option key={topic.name} value={topic.name}>
                    {topic.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mb-6">
            <button
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition duration-200 disabled:opacity-50"
              onClick={generateAdaptiveQuiz}
              disabled={loading}
            >
              {loading ? "Generating Quiz..." : "Generate Adaptive Quiz"}
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}

          {questions.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">
                Quiz Questions (Level: {userProfile?.english_level || "beginner"})
              </h3>
              {questions.map((q, index) => (
                <div key={index} className="mb-6 p-4 border rounded-lg">
                  {/* Display reading passage if it exists */}
                  {q.passage && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                      <h4 className="font-semibold text-gray-700 mb-2">Reading Passage:</h4>
                      <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                        {q.passage}
                      </p>
                    </div>
                  )}
                  <p className="font-medium mb-3">
                    {index + 1}. {q.question}
                  </p>
                  <div className="mb-2">
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {q.topic} - {q.difficulty}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {q.options.map((option, optIndex) => (
                      <label key={optIndex} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name={`question-${index}`}
                          value={option}
                          checked={answers[index] === option}
                          onChange={() => handleAnswerChange(index, option)}
                          className="text-blue-600"
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <button
                className="bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700 transition duration-200"
                onClick={handleSubmitQuiz}
                disabled={Object.keys(answers).length !== questions.length}
              >
                Submit Quiz
              </button>
            </div>
          )}
        </>
      )}

      {submitted && quizResult && (
        <div className="space-y-4">
          <div className="text-center p-6 bg-green-50 rounded-lg">
            <h3 className="text-xl font-semibold text-green-800 mb-2">Quiz Completed!</h3>
            <p className="text-lg">Your Score: <span className="font-bold">{quizResult.score}%</span></p>
            <p className="text-sm text-gray-600 mt-2">
              Current Level: <span className={`px-2 py-1 rounded text-xs font-medium ${getLevelBadgeColor(quizResult.current_level)}`}>
                {quizResult.current_level.toUpperCase()}
              </span>
            </p>
            {quizResult.level_changed && (
              <div className={`mt-3 p-3 rounded ${
                quizResult.level_change_type === 'retrocession' 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {quizResult.level_change_type === 'retrocession' 
                  ? '📉' 
                  : '🎉'
                } {quizResult.level_change_message}
                {quizResult.level_change_type === 'retrocession' && (
                  <div className="text-sm mt-1 font-medium">
                    💪 Keep practicing to improve your level again!
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold mb-2">Quiz Statistics</h4>
              <ul className="text-sm space-y-1">
                <li>Total Quizzes: {quizResult.total_quizzes}</li>
                <li>Average Score: {quizResult.average_score.toFixed(1)}%</li>
                <li>Questions Answered: {Object.keys(answers).length}</li>
              </ul>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold mb-2">Topic Performance</h4>
              {Object.entries(quizResult.topic_performance).map(([topic, perf]: [string, any]) => (
                <div key={topic} className="text-sm">
                  <span className="font-medium">{topic}:</span> {perf.correct}/{perf.total} ({Math.round((perf.correct / perf.total) * 100)}%)
                </div>
              ))}
            </div>
          </div>

          {/* Detailed Question Results */}
          <div className="space-y-4">
            <h4 className="text-xl font-semibold text-gray-800 border-b pb-2">Question Review</h4>
            {detailedResults.map((result, index) => (
              <div 
                key={index} 
                className={`p-4 rounded-lg border-2 ${
                  result.isCorrect 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    {/* Display reading passage if it exists */}
                    {result.passage && (
                      <div className="mb-4 p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                        <h6 className="font-semibold text-gray-700 mb-2">Reading Passage:</h6>
                        <p className="text-gray-700 leading-relaxed whitespace-pre-line text-sm">
                          {result.passage}
                        </p>
                      </div>
                    )}
                    <h5 className="font-medium text-gray-800 mb-2">
                      Question {index + 1}: {result.question}
                    </h5>
                    <div className="flex gap-2 mb-2">
                      <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                        {result.topic}
                      </span>
                      <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                        {result.difficulty}
                      </span>
                    </div>
                  </div>
                  <div className={`text-2xl ${result.isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                    {result.isCorrect ? '✅' : '❌'}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className={`p-3 rounded ${
                    result.isCorrect ? 'bg-green-100 border border-green-300' : 'bg-red-100 border border-red-300'
                  }`}>
                    <span className="font-medium text-gray-700">Your Answer: </span>
                    <span className={`font-semibold ${
                      result.isCorrect ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {result.userAnswer || 'No answer selected'}
                    </span>
                  </div>
                  
                  {!result.isCorrect && (
                    <div className="p-3 bg-green-100 border border-green-300 rounded">
                      <span className="font-medium text-gray-700">Correct Answer: </span>
                      <span className="font-semibold text-green-700">
                        {result.correctAnswer}
                      </span>
                    </div>
                  )}

                  {result.explanation && (
                    <div className="p-3 bg-blue-100 border border-blue-300 rounded">
                      <span className="font-medium text-gray-700">Explanation: </span>
                      <span className="text-blue-800">{result.explanation}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <button
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition duration-200 mr-4"
              onClick={() => {
                setSubmitted(false);
                setQuestions([]);
                setAnswers({});
                setQuizResult(null);
                setDetailedResults([]);
              }}
            >
              Take Another Quiz
            </button>
            <a
              href="/progress"
              className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition duration-200 inline-block"
            >
              View Progress
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdaptiveQuizPage;
