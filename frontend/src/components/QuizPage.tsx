// frontend/src/components/QuizPage.tsx
import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import apiClient from "../api/apiClient";
import { QUIZ_EVALUATION_ENDPOINT } from "../api/endpoints";

const QuizPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [submitted, setSubmitted] = useState(false);
  const [quizResult, setQuizResult] = useState<any>(null);
  const [detailedResults, setDetailedResults] = useState<any[]>([]);

  const questions = [
    {
      id: "q1",
      topic: "Grammar",
      text: "Which sentence is grammatically correct?",
      options: [
        "She don't like coffee",
        "She doesn't like coffee",
        "She don't likes coffee",
        "She doesn't likes coffee"
      ],
      correct: "She doesn't like coffee",
      explanation: "With third person singular (she/he/it), we use 'doesn't' for negative sentences in present simple tense. 'Don't' is used with I/you/we/they."
    },
    {
      id: "q2",
      topic: "Vocabulary",
      text: "What is the synonym of 'happy'?",
      options: ["Sad", "Angry", "Joyful", "Tired"],
      correct: "Joyful",
      explanation: "'Joyful' means feeling great pleasure and happiness, making it a perfect synonym for 'happy'. The other options express negative emotions or states."
    },
    {
      id: "q3",
      topic: "Grammar",
      text: "Complete the sentence: 'I _____ to London last year.'",
      options: ["go", "went", "going", "have gone"],
      correct: "went",
      explanation: "'Went' is the past tense of 'go'. We use simple past tense for completed actions in the past, especially with time markers like 'last year'."
    },
    {
      id: "q4",
      topic: "Vocabulary",
      text: "Which word means 'very large'?",
      options: ["Tiny", "Huge", "Small", "Average"],
      correct: "Huge",
      explanation: "'Huge' means extremely large or enormous. The other options refer to smaller sizes or normal size."
    },
  ];

  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleAnswerChange = (qId: string, choice: string) => {
    setAnswers({ ...answers, [qId]: choice });
  };

  const handleSubmitQuiz = async () => {
    let totalCorrect = 0;
    const quizData = questions.map((q) => {
      const userAnswer = answers[q.id];
      const isCorrect = userAnswer === q.correct;
      if (isCorrect) totalCorrect++;
      return {
        question: q.text,
        topic: q.topic,
        userAnswer,
        correctAnswer: q.correct,
        isCorrect,
        explanation: q.explanation
      };
    });

    const score = totalCorrect * 25; // 4 questions => max 100

    // Store detailed results for display
    setDetailedResults(quizData);

    try {
      const response = await apiClient.post(QUIZ_EVALUATION_ENDPOINT, {
        quiz_data: { questions: quizData },
        score,
        topic: "Mixed",
      });
      console.log("Quiz submission:", response.data);
      setQuizResult(response.data);
      setSubmitted(true);
      
      // Refresh user data to update has_completed_first_quiz status
      await refreshUser();
    } catch (err) {
      console.error("Error submitting quiz:", err);
      alert("Failed to submit quiz!");
    }
  };

  // If user has already completed their first quiz, show redirect message
  if (user?.has_completed_first_quiz) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-blue-50 border border-blue-200 rounded-lg">
        <h2 className="text-xl font-semibold text-blue-800 mb-4">
          🎉 Ready for Adaptive Learning!
        </h2>
        <p className="text-blue-700 mb-4">
          Great! You've already completed your initial assessment quiz. 
          Now it's time to continue your learning journey with our adaptive quiz system 
          that personalizes questions based on your performance and learning patterns.
        </p>
        <div className="space-y-3">
          <a
            href="/adaptive-quiz"
            className="block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition duration-200 text-center"
          >
            Take Adaptive Quiz
          </a>
          <a
            href="/progress"
            className="block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition duration-200 text-center"
          >
            View Your Progress
          </a>
          <a
            href="/chat"
            className="block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition duration-200 text-center"
          >
            Chat with AI Teacher
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow text-gray-800 max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold mb-6">AISE Assessment Quiz - Grammar & Vocabulary</h2>
      {!submitted && (
        <>
          {questions.map((q) => (
            <div key={q.id} className="mb-4">
              <p className="font-medium mb-1">
                {q.text} <span className="italic text-sm">({q.topic})</span>
              </p>
              <div className="flex flex-col space-y-1 pl-4">
                {q.options.map((opt) => (
                  <label key={opt} className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name={q.id}
                      value={opt}
                      checked={answers[q.id] === opt}
                      onChange={() => handleAnswerChange(q.id, opt)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
          <button
            className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition duration-200"
            onClick={handleSubmitQuiz}
          >
            Submit Quiz
          </button>
        </>
      )}

      {submitted && quizResult && (
        <div className="space-y-6">
          {/* Quiz Summary */}
          <div className="text-center p-6 bg-green-50 rounded-lg border border-green-200">
            <h3 className="text-2xl font-semibold text-green-800 mb-3">Quiz Completed! 🎉</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-sm text-gray-600">Your Score</p>
                <p className="text-2xl font-bold text-indigo-600">{quizResult.score}/100</p>
              </div>
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-sm text-gray-600">Questions Correct</p>
                <p className="text-2xl font-bold text-green-600">
                  {detailedResults.filter(r => r.isCorrect).length}/{detailedResults.length}
                </p>
              </div>
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-sm text-gray-600">English Level</p>
                <p className="text-lg font-bold text-purple-600 capitalize">
                  {quizResult.current_level || 'Beginner'}
                </p>
              </div>
            </div>
            
            {quizResult.level_changed && (
              <div className={`mt-4 p-4 rounded-lg border ${
                quizResult.level_change_type === 'retrocession' 
                  ? 'bg-red-100 text-red-800 border-red-300' 
                  : 'bg-green-100 text-green-800 border-green-300'
              }`}>
                <p className="font-semibold">
                  {quizResult.level_change_type === 'retrocession' 
                    ? '� Level Retrocession' 
                    : '�🚀 Level Progression'
                  }
                </p>
                <p>{quizResult.level_change_message}</p>
                {quizResult.level_change_type === 'retrocession' && (
                  <p className="text-sm mt-2 font-medium">
                    💪 Don't worry! Keep practicing and you'll improve again!
                  </p>
                )}
              </div>
            )}
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
                    <h5 className="font-medium text-gray-800 mb-2">
                      Question {index + 1}: {result.question}
                    </h5>
                    <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                      {result.topic}
                    </span>
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

          {/* Performance Breakdown */}
          {quizResult.topic_performance && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-3">Performance by Topic</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(quizResult.topic_performance).map(([topic, perf]: [string, any]) => (
                  <div key={topic} className="p-3 bg-white rounded shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-700">{topic}</span>
                      <span className="text-lg font-bold text-blue-600">
                        {perf.correct}/{perf.total}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(perf.correct / perf.total) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">
                      {Math.round((perf.correct / perf.total) * 100)}% correct
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4 pt-4">
            <button
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition duration-200"
              onClick={() => {
                setSubmitted(false);
                setAnswers({});
                setQuizResult(null);
                setDetailedResults([]);
              }}
            >
              Take Another Quiz
            </button>
            <a
              href="/progress"
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition duration-200 inline-block text-center"
            >
              View Progress
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizPage;
