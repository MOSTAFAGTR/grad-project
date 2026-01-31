import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const StudentQuizPage: React.FC = () => {
  const [step, setStep] = useState<'setup' | 'quiz' | 'result'>('setup');
  const [loading, setLoading] = useState(false);

  // Setup State
  const [topic, setTopic] = useState('SQL Injection'); // Single select for simplicity in old UI
  const [mode, setMode] = useState('Adaptive');
  const [count, setCount] = useState(5);
  const [assignments, setAssignments] = useState<any[]>([]);

  // Quiz State
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [lastResult, setLastResult] = useState<any>(null);

  const navigate = useNavigate();
  const token = sessionStorage.getItem('token');

  // Load Assignments
  useEffect(() => {
    if (token) {
      axios.get('http://localhost:8000/api/quizzes/assignments/student', {
        headers: { Authorization: `Bearer ${token}` }
      }).then(res => setAssignments(res.data))
        .catch(err => console.error(err));
    }
  }, [token]);

  const handleStartPractice = async () => {
    setLoading(true);
    try {
      // FIX: Send 'topics' as an ARRAY, not a string
      const res = await axios.post(
        'http://localhost:8000/api/quizzes/take',
        { topics: [topic], count, mode },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (res.data.length === 0) {
        alert("No questions found. Ask instructor to add some!");
      } else {
        setQuestions(res.data);
        setStep('quiz');
        setCurrentIndex(0);
        setScore(0);
      }
    } catch (err) { console.error(err); alert("Error starting quiz"); }
    setLoading(false);
  };

  const handleStartAssignment = async (id: number) => {
    try {
      const res = await axios.get(`http://localhost:8000/api/quizzes/assignments/${id}/take`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuestions(res.data);
      setStep('quiz');
      setCurrentIndex(0);
      setScore(0);
    } catch (err) { alert("Failed to start assignment"); }
  };

  const handleAnswer = async (optId: number) => {
    const res = await axios.post('http://localhost:8000/api/quizzes/submit-answer',
      { question_id: questions[currentIndex].id, selected_option_id: optId },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    setLastResult(res.data);
    if (res.data.correct) setScore(score + 1);
  };

  const handleNext = () => {
    setLastResult(null);
    if (currentIndex + 1 < questions.length) setCurrentIndex(currentIndex + 1);
    else setStep('result');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      {step === 'setup' && (
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* PRACTICE CARD */}
          <div className="bg-gray-800 p-8 rounded-lg border border-gray-700">
            <h2 className="text-2xl font-bold mb-6 text-blue-400">Practice Mode</h2>
            <div className="mb-4">
              <label className="block text-gray-300 mb-2">Topic</label>
              <select className="w-full bg-gray-700 p-2 rounded text-white" value={topic} onChange={e => setTopic(e.target.value)}>
                <option>SQL Injection</option>
                <option>XSS</option>
                <option>Authentication</option>
              </select>
            </div>
            <div className="mb-6">
              <label className="block text-gray-300 mb-2">Mode</label>
              <div className="flex gap-4">
                <button onClick={() => setMode('Adaptive')} className={`flex-1 py-2 rounded border ${mode === 'Adaptive' ? 'bg-purple-600 border-purple-600' : 'bg-gray-700 border-gray-600'}`}>Adaptive (AI)</button>
                <button onClick={() => setMode('Practice')} className={`flex-1 py-2 rounded border ${mode === 'Practice' ? 'bg-blue-600 border-blue-600' : 'bg-gray-700 border-gray-600'}`}>Standard</button>
              </div>
            </div>
            <button onClick={handleStartPractice} disabled={loading} className="w-full bg-blue-600 py-3 rounded font-bold hover:bg-blue-700 transition">
              {loading ? "Loading..." : "Start Practice"}
            </button>
          </div>

          {/* ASSIGNMENTS CARD */}
          <div className="bg-gray-800 p-8 rounded-lg border border-purple-900">
            <h2 className="text-2xl font-bold mb-6 text-purple-400">My Assignments</h2>
            {assignments.length === 0 ? <p className="text-gray-500">No assignments pending.</p> : (
              <div className="space-y-3">
                {assignments.map(a => (
                  <div key={a.id} className="bg-gray-700 p-4 rounded flex justify-between items-center">
                    <span className="font-bold">{a.title}</span>
                    <button onClick={() => handleStartAssignment(a.id)} className="bg-purple-600 px-3 py-1 rounded text-sm hover:bg-purple-700 font-bold">Start</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* QUIZ VIEW */}
      {step === 'quiz' && questions.length > 0 && (
        <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 max-w-2xl w-full shadow-2xl">
          <div className="flex justify-between mb-6 text-gray-400">
            <span>Q {currentIndex + 1} / {questions.length}</span>
            <span className="bg-gray-700 px-2 rounded text-xs py-1">{questions[currentIndex].difficulty}</span>
          </div>
          <h2 className="text-2xl font-bold mb-8">{questions[currentIndex].text}</h2>
          <div className="space-y-3">
            {questions[currentIndex].options.map((opt: any) => (
              <button key={opt.id} onClick={() => handleAnswer(opt.id)} disabled={lastResult !== null}
                className={`w-full text-left p-4 rounded border transition ${lastResult ? 'bg-gray-700 opacity-70' : 'bg-gray-700 hover:border-blue-500'}`}>
                {opt.text}
              </button>
            ))}
          </div>
          {lastResult && (
            <div className={`mt-6 p-4 rounded border ${lastResult.correct ? "bg-green-900/30 border-green-500" : "bg-red-900/30 border-red-500"}`}>
              <h3 className={`font-bold ${lastResult.correct ? "text-green-400" : "text-red-400"}`}>{lastResult.correct ? "Correct!" : "Incorrect"}</h3>
              <p className="text-sm mt-1 text-gray-300">{lastResult.explanation}</p>
              <button onClick={handleNext} className="mt-4 bg-gray-600 px-6 py-2 rounded hover:bg-gray-500 w-full">Next</button>
            </div>
          )}
        </div>
      )}

      {/* RESULT VIEW */}
      {step === 'result' && (
        <div className="bg-gray-800 p-10 rounded-xl text-center shadow-2xl">
          <h2 className="text-4xl font-bold text-white mb-4">Quiz Finished</h2>
          <div className="text-6xl font-extrabold text-blue-500 mb-6">{Math.round((score / questions.length) * 100)}%</div>
          <button onClick={() => setStep('setup')} className="bg-gray-700 px-8 py-3 rounded font-bold hover:bg-gray-600">Back to Dashboard</button>
        </div>
      )}
    </div>
  );
};

export default StudentQuizPage;