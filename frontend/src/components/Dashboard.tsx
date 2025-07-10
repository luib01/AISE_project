// frontend/src/components/Dashboard.tsx
import React, { useEffect, useRef, useState } from "react";
import Chart, { ChartDataset } from "chart.js/auto";
import apiClient from "../api/apiClient";
import { USER_PERFORMANCE_DETAILED_ENDPOINT } from "../api/endpoints";
import { useAuth } from "../contexts/AuthContext";

interface QuizResult {
  quiz_number: number;
  score: number;
  topic: string;
  difficulty: string;
  timestamp: string;
}

interface TopicPerformance {
  percentage: number;
  correct: number;
  total: number;
}

interface UserPerformance {
  user_id: string;
  english_level: string;
  total_quizzes: number;
  average_score: number;
  topic_performance: Record<string, TopicPerformance>;
  recent_quizzes: QuizResult[];
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [performanceData, setPerformanceData] = useState<UserPerformance | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const generalChartRef = useRef<Chart | null>(null);
  const topicChartRefs = useRef<Record<string, Chart>>({});

  const fetchPerformanceData = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiClient.get(USER_PERFORMANCE_DETAILED_ENDPOINT);
      setPerformanceData(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch performance data.");
      setPerformanceData(null);
    } finally {
      setLoading(false);
    }
  };

  // Automatically load data when component mounts
  useEffect(() => {
    if (user) {
      fetchPerformanceData();
    }
  }, [user]);

  const createGeneralLineplot = () => {
    if (!performanceData || !performanceData.recent_quizzes.length) return;

    // Destroy existing chart
    if (generalChartRef.current) {
      generalChartRef.current.destroy();
    }

    const canvas = document.getElementById("generalProgressChart") as HTMLCanvasElement;
    if (!canvas) return;

    // Data is already sorted chronologically from the backend
    const data = performanceData.recent_quizzes.map(quiz => ({
      x: quiz.quiz_number, // Use quiz_number from backend
      y: quiz.score,
      topic: quiz.topic,
      difficulty: quiz.difficulty,
      timestamp: new Date(quiz.timestamp).toLocaleDateString()
    }));

    // Debug logging
    console.log('Dashboard: Recent quizzes data:', performanceData.recent_quizzes);
    console.log('Dashboard: Mapped chart data:', data);

    // Group data by difficulty for multiple lines
    const beginnerData = data.filter(point => point.difficulty.toLowerCase() === 'beginner');
    const intermediateData = data.filter(point => point.difficulty.toLowerCase() === 'intermediate');
    const advancedData = data.filter(point => point.difficulty.toLowerCase() === 'advanced');

    const datasets: ChartDataset<'line', { x: number; y: number; topic: string; difficulty: string; timestamp: string; }[]>[] = [];

    if (beginnerData.length > 0) {
      datasets.push({
        label: 'Beginner Level',
        data: beginnerData,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 6,
        pointHoverRadius: 8
      });
    }

    if (intermediateData.length > 0) {
      datasets.push({
        label: 'Intermediate Level',
        data: intermediateData,
        borderColor: 'rgba(255, 206, 86, 1)',
        backgroundColor: 'rgba(255, 206, 86, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 6,
        pointHoverRadius: 8
      });
    }

    if (advancedData.length > 0) {
      datasets.push({
        label: 'Advanced Level',
        data: advancedData,
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 6,
        pointHoverRadius: 8
      });
    }

    generalChartRef.current = new Chart(canvas, {
      type: 'line',
      data: {
        datasets: datasets
      },
      options: {
        responsive: true,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Quiz Number'
            },
            type: 'linear',
            beginAtZero: false
          },
          y: {
            title: {
              display: true,
              text: 'Score (%)'
            },
            beginAtZero: true,
            max: 100
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context: any) {
                const point = context.raw;
                return [
                  `Score: ${point.y}%`,
                  `Topic: ${point.topic}`,
                  `Difficulty: ${point.difficulty}`,
                  `Date: ${point.timestamp}`
                ];
              }
            }
          },
          legend: {
            display: true,
            position: 'top'
          }
        }
      }
    });
  };

  const createTopicLineplots = () => {
    if (!performanceData || !performanceData.recent_quizzes.length) return;

    // Clear existing topic charts
    Object.values(topicChartRefs.current).forEach(chart => chart.destroy());
    topicChartRefs.current = {};

    // Group quizzes by topic
    const topicData: Record<string, QuizResult[]> = {};
    performanceData.recent_quizzes.forEach(quiz => {
      if (!topicData[quiz.topic]) {
        topicData[quiz.topic] = [];
      }
      topicData[quiz.topic].push(quiz);
    });

    // Create a chart for each topic
    Object.entries(topicData).forEach(([topic, quizzes]) => {
      const canvas = document.getElementById(`topic-${topic.replace(/\s+/g, '-')}`) as HTMLCanvasElement;
      if (!canvas) return;

      const sortedQuizzes = [...quizzes].sort((a, b) => a.quiz_number - b.quiz_number);

      const data = sortedQuizzes.map(quiz => ({
        x: quiz.quiz_number,
        y: quiz.score,
        difficulty: quiz.difficulty,
        timestamp: new Date(quiz.timestamp).toLocaleDateString()
      }));

      const beginnerData = data.filter(point => point.difficulty.toLowerCase() === 'beginner');
      const intermediateData = data.filter(point => point.difficulty.toLowerCase() === 'intermediate');
      const advancedData = data.filter(point => point.difficulty.toLowerCase() === 'advanced');

      const datasets: ChartDataset<'line', { x: number; y: number; difficulty: string; timestamp: string; }[]>[] = [];

      if (beginnerData.length > 0) {
        datasets.push({
          label: 'Beginner',
          data: beginnerData,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7
        });
      }

      if (intermediateData.length > 0) {
        datasets.push({
          label: 'Intermediate',
          data: intermediateData,
          borderColor: 'rgba(255, 206, 86, 1)',
          backgroundColor: 'rgba(255, 206, 86, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7
        });
      }

      if (advancedData.length > 0) {
        datasets.push({
          label: 'Advanced',
          data: advancedData,
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7
        });
      }

      topicChartRefs.current[topic] = new Chart(canvas, {
        type: 'line',
        data: {
          datasets: datasets
        },
        options: {
          responsive: true,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Quiz Number'
              },
              type: 'linear', // Use linear scale for quiz numbers
              beginAtZero: false
            },
            y: {
              title: {
                display: true,
                text: 'Score (%)'
              },
              beginAtZero: true,
              max: 100
            }
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: function(context: any) {
                  const point = context.raw;
                  return [
                    `Quiz #${point.x}`,
                    `Score: ${point.y}%`,
                    `Difficulty: ${point.difficulty}`,
                    `Date: ${point.timestamp}`
                  ];
                }
              }
            },
            legend: {
              display: true,
              position: 'top'
            },
            title: {
              display: true,
              text: `${topic} Progress`,
              font: {
                size: 16
              }
            }
          }
        }
      });
    });
  };

  useEffect(() => {
    if (performanceData) {
      // Small delay to ensure DOM elements are rendered
      setTimeout(() => {
        createGeneralLineplot();
        createTopicLineplots();
      }, 100);
    }
  }, [performanceData]);

  const getLevelBadgeColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow text-gray-800 max-w-7xl mx-auto">
      <h2 className="text-3xl font-semibold mb-6">Progress Dashboard</h2>
      
      {loading && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-600">Loading your progress data...</p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {performanceData && (
        <>
          {/* Summary Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="font-semibold text-blue-800">Current Level</h3>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium mt-2 ${getLevelBadgeColor(performanceData.english_level)}`}>
                {performanceData.english_level.toUpperCase()}
              </span>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h3 className="font-semibold text-green-800">Total Quizzes</h3>
              <p className="text-2xl font-bold text-green-700 mt-2">{performanceData.total_quizzes}</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <h3 className="font-semibold text-purple-800">Average Score</h3>
              <p className="text-2xl font-bold text-purple-700 mt-2">{performanceData.average_score.toFixed(1)}%</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <h3 className="font-semibold text-yellow-800">Topics Practiced</h3>
              <p className="text-2xl font-bold text-yellow-700 mt-2">{Object.keys(performanceData.topic_performance).length}</p>
            </div>
          </div>

          {/* General Progress Scatterplot */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold mb-4">Overall Progress Timeline</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="mb-4">
                <div className="flex gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <span>Beginner</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <span>Intermediate</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <span>Advanced</span>
                  </div>
                </div>
              </div>
              <div style={{ height: '400px' }}>
                <canvas id="generalProgressChart"></canvas>
              </div>
            </div>
          </div>

          {/* Topic-specific Progress */}
          {Object.keys(performanceData.topic_performance).length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-4">Progress by Topic</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                {performanceData && Object.entries(performanceData.topic_performance).map(([topic, performance]) => (
                  <div key={topic} className="bg-white p-6 rounded-lg shadow-lg">
                    <h4 className="text-lg font-semibold mb-2 text-gray-600">{topic}</h4>
                    <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                      <div
                        className="bg-blue-500 h-4 rounded-full"
                        style={{ width: `${(performance as TopicPerformance).percentage}%` }}
                      ></div>
                    </div>
                    <p className="text-right text-sm text-gray-600">
                      {(performance as TopicPerformance).correct}/{(performance as TopicPerformance).total} ({(performance as TopicPerformance).percentage}%)
                    </p>
                    <div className="mt-4">
                      <canvas id={`topic-${topic.replace(/\s+/g, '-')}`}></canvas>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!performanceData && !loading && !error && (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">
            Click "Load Progress" to view your learning analytics.
          </p>
          <p className="text-gray-500 mt-2">
            Take some quizzes first to see your progress data!
          </p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
