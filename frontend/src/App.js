import React, { useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [topic, setTopic] = useState("OSI Layers");
  const [ageGroup, setAgeGroup] = useState("adult");
  const [difficulty, setDifficulty] = useState("beginner");
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const generateLesson = async () => {
    setLoading(true);
    setError(null);
    setLesson(null);
    setShowQuiz(false);
    setShowResults(false);
    setUserAnswers({});

    try {
      const response = await axios.post(`${API}/generate-lesson`, {
        topic,
        age_group: ageGroup,
        difficulty,
      });
      setLesson(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate lesson");
    } finally {
      setLoading(false);
    }
  };

  const handleQuizAnswer = (questionIndex, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionIndex]: answer
    }));
  };

  const submitQuiz = () => {
    setShowResults(true);
  };

  const calculateScore = () => {
    if (!lesson?.quiz) return 0;
    let correct = 0;
    lesson.quiz.forEach((question, index) => {
      if (userAnswers[index] === question.correct_answer) {
        correct++;
      }
    });
    return Math.round((correct / lesson.quiz.length) * 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 rounded-lg">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">TechTales</h1>
                <p className="text-gray-600">AI-Powered Educational Stories</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Input Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Your Learning Experience</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Topic Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Topic</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., OSI Layers, DBMS Transactions"
              />
            </div>

            {/* Age Group */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Age Group</label>
              <select
                value={ageGroup}
                onChange={(e) => setAgeGroup(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="child">Child (6-12)</option>
                <option value="teen">Teen (13-17)</option>
                <option value="adult">Adult (18+)</option>
              </select>
            </div>

            {/* Difficulty */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>

          <button
            onClick={generateLesson}
            disabled={loading}
            className="mt-6 w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            {loading ? (
              <div className="flex items-center justify-center space-x-2">
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Creating your lesson...</span>
              </div>
            ) : (
              "Generate Lesson"
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Lesson Display */}
        {lesson && (
          <div className="space-y-8">
            {/* Story Section */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <svg className="w-6 h-6 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Learning Story: {lesson.topic}
              </h2>
              
              <div className="prose prose-lg max-w-none text-gray-700 leading-relaxed">
                {lesson.story.split('\n').map((paragraph, index) => (
                  <p key={index} className="mb-4">{paragraph}</p>
                ))}
              </div>
            </div>

            {/* Images Section */}
            {lesson.images && lesson.images.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <svg className="w-6 h-6 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Visual Illustrations
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {lesson.images.map((image, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={`data:image/png;base64,${image}`}
                        alt={`Illustration ${index + 1}`}
                        className="w-full h-64 object-cover rounded-lg shadow-md group-hover:shadow-xl transition-shadow duration-300"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 rounded-lg flex items-center justify-center">
                        <p className="text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-center px-4">
                          {lesson.visual_cues[index]}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quiz Section */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <svg className="w-6 h-6 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Knowledge Check
                </h2>
                
                {!showQuiz && (
                  <button
                    onClick={() => setShowQuiz(true)}
                    className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors duration-200"
                  >
                    Take Quiz
                  </button>
                )}
              </div>

              {showQuiz && (
                <div className="space-y-6">
                  {lesson.quiz.map((question, questionIndex) => (
                    <div key={questionIndex} className="border border-gray-200 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        {questionIndex + 1}. {question.question}
                      </h3>
                      
                      <div className="space-y-3">
                        {question.options.map((option, optionIndex) => (
                          <label
                            key={optionIndex}
                            className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                              userAnswers[questionIndex] === option
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <input
                              type="radio"
                              name={`question-${questionIndex}`}
                              value={option}
                              checked={userAnswers[questionIndex] === option}
                              onChange={() => handleQuizAnswer(questionIndex, option)}
                              className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
                              userAnswers[questionIndex] === option
                                ? 'border-blue-500 bg-blue-500'
                                : 'border-gray-300'
                            }`}>
                              {userAnswers[questionIndex] === option && (
                                <div className="w-2 h-2 bg-white rounded-full"></div>
                              )}
                            </div>
                            <span className="text-gray-700">{option}</span>
                          </label>
                        ))}
                      </div>

                      {/* Show explanation if results are shown */}
                      {showResults && (
                        <div className={`mt-4 p-4 rounded-lg ${
                          userAnswers[questionIndex] === question.correct_answer
                            ? 'bg-green-50 border border-green-200'
                            : 'bg-red-50 border border-red-200'
                        }`}>
                          <p className={`font-semibold mb-2 ${
                            userAnswers[questionIndex] === question.correct_answer
                              ? 'text-green-800'
                              : 'text-red-800'
                          }`}>
                            {userAnswers[questionIndex] === question.correct_answer ? 'Correct!' : 'Incorrect'}
                          </p>
                          <p className="text-gray-700">
                            <strong>Correct Answer:</strong> {question.correct_answer}
                          </p>
                          <p className="text-gray-700 mt-2">
                            <strong>Explanation:</strong> {question.explanation}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}

                  {!showResults && (
                    <button
                      onClick={submitQuiz}
                      disabled={Object.keys(userAnswers).length < lesson.quiz.length}
                      className="w-full bg-green-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    >
                      Submit Quiz
                    </button>
                  )}

                  {showResults && (
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 text-center">
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">Quiz Complete!</h3>
                      <p className="text-lg text-gray-700 mb-4">
                        Your Score: <span className="font-bold text-blue-600">{calculateScore()}%</span>
                      </p>
                      <p className="text-gray-600">
                        You got {Object.keys(userAnswers).filter(key => userAnswers[key] === lesson.quiz[key].correct_answer).length} out of {lesson.quiz.length} questions correct.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;