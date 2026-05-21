import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useScanContext } from '../context/ScanContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const BANK_TOPICS = [
  'SQL Injection',
  'XSS',
  'CSRF',
  'Command Injection',
  'Broken Authentication',
  'Directory Traversal',
  'XXE',
  'Insecure Storage',
  'Security Misconfiguration',
];

function filterFindingsForScan(findings: any[], focus: 'all' | 'highest'): any[] {
  if (!findings.length) return [];
  if (focus === 'all') return findings;
  const order: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 };
  const scored = findings.map((f) => ({
    f,
    s: order[String(f.severity || '').toLowerCase()] || 0,
  }));
  const maxS = Math.max(...scored.map((x) => x.s));
  if (maxS === 0) return findings;
  return scored.filter((x) => x.s === maxS).map((x) => x.f);
}

const StudentQuizPage: React.FC = () => {
  const { scanData } = useScanContext();
  const [step, setStep] = useState<'setup' | 'quiz' | 'result'>('setup');
  const [loading, setLoading] = useState(false);

  const [topicFilter, setTopicFilter] = useState('All topics');
  const [standardCount, setStandardCount] = useState(10);
  const [standardDifficulty, setStandardDifficulty] = useState<'Any' | 'Easy' | 'Medium' | 'Hard'>('Any');

  const [scanQuizCount, setScanQuizCount] = useState(8);
  const [scanFocus, setScanFocus] = useState<'all' | 'highest'>('all');
  const [assignments, setAssignments] = useState<any[]>([]);
  const [quizTitle, setQuizTitle] = useState('');
  const [assignmentId, setAssignmentId] = useState<number | null>(null);
  const [generatedFromScan, setGeneratedFromScan] = useState(false);

  const [questions, setQuestions] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [score, setScore] = useState(0);
  const scoreRef = useRef(0);
  const [wrongCategories, setWrongCategories] = useState<string[]>([]);
  const [lastResult, setLastResult] = useState<any>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
  const [assignmentDueDate, setAssignmentDueDate] = useState<string | null>(null);
  const [timesUp, setTimesUp] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const endTimeRef = useRef<number | null>(null);
  const autoSubmittedRef = useRef(false);
  const [wrongAnswerInfo, setWrongAnswerInfo] = useState<{ count: number; enough: boolean } | null>(null);
  const [generatingMistakes, setGeneratingMistakes] = useState(false);
  const [mistakesError, setMistakesError] = useState<string | null>(null);
  const [isMistakesQuiz, setIsMistakesQuiz] = useState(false);

  const difficultyLevel: 'Beginner' | 'Intermediate' | 'Advanced' = 'Intermediate';

  const token = sessionStorage.getItem('token');

  const scanFindingsRaw = scanData?.findings || scanData?.results?.findings || [];
  const hasScanData = Array.isArray(scanFindingsRaw) && scanFindingsRaw.length > 0;
  const scanProjectLabel =
    (scanData as any)?.overview?.name ||
    (scanData as any)?.results?.project_name ||
    scanData?.projectId ||
    'Project';

  useEffect(() => {
    if (token) {
      axios
        .get(`${API_URL}/api/quizzes/wrong-answer-count`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((res) => setWrongAnswerInfo({ count: res.data.count, enough: res.data.enough }))
        .catch(() => setWrongAnswerInfo(null));
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      axios
        .get(`${API_URL}/api/quizzes/assignments/student`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((res) => setAssignments(res.data))
        .catch((err) => console.error(err));
    }
  }, [token]);

  useEffect(() => {
    if (step === 'quiz' && questions.length > 0) {
      setElapsedSeconds(0);
      timerRef.current = setInterval(() => {
        setElapsedSeconds((s) => s + 1);
        if (endTimeRef.current != null) {
          const left = Math.max(0, Math.floor((endTimeRef.current - Date.now()) / 1000));
          setRemainingSeconds(left);
          if (left <= 0) setTimesUp(true);
        }
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [step, questions.length]);

  const finishQuiz = React.useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    setStep('result');
    if (!token || questions.length === 0) return;
    if (assignmentId) {
      if (autoSubmittedRef.current) return;
      autoSubmittedRef.current = true;
    }
    axios
      .post(
        `${API_URL}/api/quizzes/submit-attempt`,
        {
          assignment_id: assignmentId,
          title: quizTitle || 'Quiz',
          score: scoreRef.current,
          total: questions.length,
          time_seconds: elapsedSeconds + 1,
        },
        { headers: { Authorization: `Bearer ${token}` } },
      )
      .catch(() => {});
  }, [assignmentId, elapsedSeconds, questions.length, quizTitle, token]);

  useEffect(() => {
    if (timesUp && step === 'quiz' && assignmentId) {
      finishQuiz();
    }
  }, [timesUp, step, assignmentId, finishQuiz]);

  const handleStartStandardQuiz = async () => {
    setLoading(true);
    try {
      const topics = topicFilter === 'All topics' ? BANK_TOPICS : [topicFilter];
      const body: {
        topics: string[];
        count: number;
        mode: string;
        difficulty?: string;
      } = {
        topics,
        count: standardCount,
        mode: 'Practice',
      };
      if (standardDifficulty !== 'Any') {
        body.difficulty = standardDifficulty;
      }
      const res = await axios.post(`${API_URL}/api/quizzes/take`, body, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.data.length === 0) {
        alert('No questions found. Ask instructor to add some!');
      } else {
        setQuestions(res.data);
        setQuizTitle(topicFilter === 'All topics' ? 'Standard Quiz (all topics)' : `Standard Quiz: ${topicFilter}`);
        setAssignmentId(null);
        setGeneratedFromScan(false);
        setIsMistakesQuiz(false);
        setStep('quiz');
        setCurrentIndex(0);
        setScore(0);
        scoreRef.current = 0;
        setWrongCategories([]);
      }
    } catch (err) {
      console.error(err);
      alert('Error starting quiz');
    }
    setLoading(false);
  };

  const handleGenerateScanQuiz = async () => {
    if (!token) return;
    const findings = filterFindingsForScan(scanFindingsRaw, scanFocus).slice(0, scanQuizCount);
    if (findings.length === 0) {
      alert('No scan findings available. Run scanner first.');
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(
        `${API_URL}/api/quiz/generate`,
        { findings, difficulty: difficultyLevel, category: 'Adaptive', explanation_depth: 'detailed' },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const generated = (res.data?.questions || []).map((q: any, idx: number) => ({
        id: idx + 100000,
        text: q.question || q.prompt,
        difficulty: q.difficulty || difficultyLevel,
        difficulty_score: q.difficulty_score || 2,
        explanation: q.explanation,
        category: q.category || 'General',
        question_type: q.type || 'MCQ',
        options: (q.options || []).map((opt: string, oidx: number) => ({
          id: idx * 10 + oidx + 1,
          text: opt,
          is_correct: opt === (q.correct_answer || q.answer),
        })),
      }));
      if (generated.length === 0) {
        alert('Could not generate quiz from findings.');
      } else {
        setQuestions(generated);
        setQuizTitle(`Quiz from scan (${scanFocus === 'highest' ? 'highest severity' : 'all findings'})`);
        setAssignmentId(null);
        setGeneratedFromScan(true);
        setIsMistakesQuiz(false);
        setStep('quiz');
        setCurrentIndex(0);
        setScore(0);
        scoreRef.current = 0;
        setWrongCategories([]);
      }
    } catch {
      alert('Failed to generate dynamic quiz.');
    } finally {
      setLoading(false);
    }
  };

  const handleMistakesQuiz = async () => {
    if (!token) return;
    setGeneratingMistakes(true);
    setMistakesError(null);
    try {
      const res = await axios.post(
        `${API_URL}/api/quizzes/common-mistakes-quiz`,
        {},
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const raw = res.data?.questions || [];
      if (raw.length === 0) {
        setMistakesError('No questions returned. Try again later.');
        return;
      }
      setQuestions(raw);
      setQuizTitle('Common Mistakes Quiz');
      setAssignmentId(null);
      setGeneratedFromScan(false);
      setIsMistakesQuiz(true);
      setStep('quiz');
      setCurrentIndex(0);
      setScore(0);
      scoreRef.current = 0;
      setWrongCategories([]);
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      const d = ax.response?.data?.detail;
      setMistakesError(typeof d === 'string' ? d : 'Failed to generate quiz');
    } finally {
      setGeneratingMistakes(false);
    }
  };

  const handleStartAssignment = async (id: number, title: string) => {
    try {
      autoSubmittedRef.current = false;
      setTimesUp(false);
      endTimeRef.current = null;
      setRemainingSeconds(null);
      setAssignmentDueDate(null);

      const startRes = await axios.post(
        `${API_URL}/api/quizzes/assignments/${id}/start`,
        {},
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const startData = startRes.data;
      if (startData.due_date) setAssignmentDueDate(startData.due_date);
      if (startData.time_limit_seconds) {
        endTimeRef.current = Date.now() + startData.time_limit_seconds * 1000;
        setRemainingSeconds(startData.time_limit_seconds);
      }

      const res = await axios.get(`${API_URL}/api/quizzes/assignments/${id}/take`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setQuestions(res.data);
      setQuizTitle(title);
      setAssignmentId(id);
      setGeneratedFromScan(false);
      setIsMistakesQuiz(false);
      setStep('quiz');
      setCurrentIndex(0);
      setScore(0);
      scoreRef.current = 0;
      setWrongCategories([]);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      alert(ax.response?.data?.detail || 'Failed to start assignment');
    }
  };

  const handleAnswer = async (optId: number) => {
    const current = questions[currentIndex];
    if (Number(current?.id) >= 100000) {
      const selected = (current.options || []).find((o: any) => o.id === optId);
      const correct = Boolean(selected?.is_correct);
      const localResult = { correct, explanation: current.explanation || 'Review secure coding principles.' };
      setLastResult(localResult);
      if (correct) {
        setScore((prev) => {
          const next = prev + 1;
          scoreRef.current = next;
          return next;
        });
      } else {
        setWrongCategories((prev) => [...prev, current?.category || 'General']);
      }
      return;
    }
    const res = await axios.post(
      `${API_URL}/api/quizzes/submit-answer`,
      { question_id: current.id, selected_option_id: optId },
      { headers: { Authorization: `Bearer ${token}` } },
    );
    setLastResult(res.data);
    if (res.data.correct) {
      setScore((prev) => {
        const next = prev + 1;
        scoreRef.current = next;
        return next;
      });
    } else {
      setWrongCategories((prev) => [...prev, current?.category || 'General']);
    }
  };

  const handleNext = () => {
    setLastResult(null);
    if (currentIndex + 1 < questions.length) setCurrentIndex(currentIndex + 1);
    else finishQuiz();
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  const cardStyle: React.CSSProperties = {
    backgroundColor: '#111827',
    border: '1px solid #374151',
    borderRadius: 12,
    padding: 24,
    flex: '1 1 300px',
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      {step === 'setup' && (
        <div className="w-full max-w-5xl">
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '32px' }}>
            <div style={cardStyle}>
              <h2 style={{ fontWeight: 700, fontSize: 18, marginBottom: 12 }}>Standard Quiz</h2>
              <p className="text-gray-400 text-sm mb-4">
                Answer questions from the SCALE security question bank covering all vulnerability types.
              </p>
              <label className="block text-gray-300 text-sm mb-1">Number of questions</label>
              <input
                type="number"
                min={5}
                max={30}
                value={standardCount}
                onChange={(e) => setStandardCount(Number(e.target.value))}
                className="w-full bg-gray-700 p-2 rounded text-white mb-3 border border-gray-600"
              />
              <label className="block text-gray-300 text-sm mb-1">Topic filter</label>
              <select
                className="w-full bg-gray-700 p-2 rounded text-white mb-3 border border-gray-600"
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
              >
                <option value="All topics">All topics</option>
                {BANK_TOPICS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <label className="block text-gray-300 text-sm mb-1">Difficulty</label>
              <select
                className="w-full bg-gray-700 p-2 rounded text-white mb-4 border border-gray-600"
                value={standardDifficulty}
                onChange={(e) => setStandardDifficulty(e.target.value as typeof standardDifficulty)}
              >
                <option value="Any">Any</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
              <button
                onClick={handleStartStandardQuiz}
                disabled={loading}
                className="w-full bg-blue-600 py-3 rounded font-bold hover:bg-blue-700 transition"
              >
                {loading ? 'Loading...' : 'Start Standard Quiz'}
              </button>
            </div>

            <div style={cardStyle}>
              <h2 style={{ fontWeight: 700, fontSize: 18, marginBottom: 12 }}>Quiz from My Last Scan</h2>
              <p className="text-gray-400 text-sm mb-4">
                Generate questions tailored to vulnerabilities found in your last scanned project.
              </p>
              {hasScanData ? (
                <div className="mb-4 px-3 py-2 rounded-lg bg-emerald-900/40 border border-emerald-700 text-emerald-200 text-sm">
                  Scan available: {scanProjectLabel}
                </div>
              ) : (
                <div className="mb-4 px-3 py-2 rounded-lg bg-amber-900/40 border border-amber-600 text-amber-200 text-sm">
                  No scan — upload a project first
                </div>
              )}
              <label className="block text-gray-300 text-sm mb-1">Number of questions</label>
              <input
                type="number"
                min={3}
                max={20}
                value={scanQuizCount}
                onChange={(e) => setScanQuizCount(Number(e.target.value))}
                className="w-full bg-gray-700 p-2 rounded text-white mb-3 border border-gray-600"
                disabled={!hasScanData}
              />
              <label className="block text-gray-300 text-sm mb-1">Focus area</label>
              <select
                className="w-full bg-gray-700 p-2 rounded text-white mb-4 border border-gray-600"
                value={scanFocus}
                onChange={(e) => setScanFocus(e.target.value as 'all' | 'highest')}
                disabled={!hasScanData}
              >
                <option value="all">All findings</option>
                <option value="highest">Highest severity only</option>
              </select>
              <button
                onClick={handleGenerateScanQuiz}
                disabled={loading || !hasScanData}
                className="w-full bg-purple-600 py-3 rounded font-bold hover:bg-purple-700 transition disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Generate Scan Quiz'}
              </button>
            </div>

            <div style={cardStyle}>
              <h2 style={{ fontWeight: 700, fontSize: 18, marginBottom: 12 }}>Common Mistakes Quiz</h2>
              <p className="text-gray-400 text-sm mb-4">
                Personalized to YOUR wrong answers. Our AI analyzes your quiz history to find patterns in your
                mistakes, then generates targeted questions to fix your specific knowledge gaps.
              </p>
              {wrongAnswerInfo && wrongAnswerInfo.count >= 3 && (
                <div className="mb-4 px-3 py-2 rounded-lg bg-cyan-900/40 border border-cyan-700 text-cyan-200 text-sm">
                  {wrongAnswerInfo.count} wrong answers analyzed
                </div>
              )}
              {wrongAnswerInfo && wrongAnswerInfo.count < 3 && (
                <div className="mb-4 px-3 py-2 rounded-lg bg-amber-900/40 border border-amber-600 text-amber-200 text-sm">
                  Complete more quizzes first
                </div>
              )}
              {mistakesError && (
                <div className="mb-3 text-sm text-red-400 border border-red-800 rounded p-2">{mistakesError}</div>
              )}
              <button
                onClick={handleMistakesQuiz}
                disabled={generatingMistakes || !wrongAnswerInfo?.enough}
                className="w-full bg-teal-600 py-3 rounded font-bold hover:bg-teal-500 transition disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {generatingMistakes ? 'Analyzing your mistakes...' : 'Generate My Mistakes Quiz'}
              </button>
            </div>
          </div>

          <div className="bg-gray-800 p-8 rounded-lg border border-purple-900">
            <h2 className="text-2xl font-bold mb-6 text-purple-400">My Assignments</h2>
            {assignments.length === 0 ? (
              <p className="text-gray-500">No assignments pending.</p>
            ) : (
              <div className="space-y-3">
                {assignments.map((a) => {
                  const pastDue = a.is_past_due === true;
                  const done = a.status === 'completed' || a.status === 'expired';
                  return (
                    <div key={a.id} className="bg-gray-700 p-4 rounded flex justify-between items-center gap-3">
                      <div>
                        <span className="font-bold block">{a.title}</span>
                        <span className="text-xs text-gray-400">
                          {a.time_limit_minutes ? `${a.time_limit_minutes} min timer` : 'No timer'}
                          {a.due_date ? ` · Due ${new Date(a.due_date).toLocaleDateString()}` : ''}
                          {a.status && a.status !== 'assigned' ? ` · ${a.status}` : ''}
                        </span>
                      </div>
                      <button
                        onClick={() => handleStartAssignment(a.id, a.title)}
                        disabled={pastDue || done}
                        className="bg-purple-600 px-3 py-1 rounded text-sm hover:bg-purple-700 font-bold disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                      >
                        {done ? 'Done' : pastDue ? 'Expired' : 'Start'}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {step === 'quiz' && questions.length > 0 && (
        <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 max-w-2xl w-full shadow-2xl">
          <div className="w-full h-2 bg-gray-700 rounded mb-4 overflow-hidden">
            <div
              className="h-2 bg-blue-500"
              style={{ width: `${Math.round(((currentIndex + 1) / questions.length) * 100)}%` }}
            />
          </div>
          {generatedFromScan && (
            <div className="mb-4 text-xs bg-purple-900/40 border border-purple-700 text-purple-200 rounded px-3 py-2">
              Based on your uploaded project vulnerabilities
            </div>
          )}
          {isMistakesQuiz && (
            <div className="mb-4 text-xs bg-teal-900/40 border border-teal-700 text-teal-200 rounded px-3 py-2">
              Common mistakes — targeted to your recent wrong answers
            </div>
          )}
          <div className="flex justify-between items-center mb-6 text-gray-400">
            <span>
              Question {currentIndex + 1} / {questions.length}
            </span>
            <div className="flex gap-3 items-center flex-wrap justify-end">
              {assignmentId && remainingSeconds != null && (
                <span
                  className={`px-3 py-1 rounded text-sm font-mono ${
                    remainingSeconds <= 60 ? 'bg-red-900/60 text-red-200' : 'bg-amber-900/50 text-amber-300'
                  }`}
                >
                  {formatTime(remainingSeconds)} left
                </span>
              )}
              {assignmentId && remainingSeconds == null && (
                <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded text-sm font-mono">
                  {formatTime(elapsedSeconds)} elapsed
                </span>
              )}
              {!assignmentId && (
                <span className="bg-amber-900/50 text-amber-300 px-3 py-1 rounded text-sm font-mono">
                  {formatTime(elapsedSeconds)}
                </span>
              )}
              {assignmentDueDate && (
                <span className="text-xs text-gray-400">Due {new Date(assignmentDueDate).toLocaleString()}</span>
              )}
              <span className="bg-gray-700 px-2 rounded text-xs py-1">{questions[currentIndex].difficulty}</span>
              <span className="bg-purple-900/40 text-purple-200 px-2 rounded text-xs py-1">
                {questions[currentIndex].question_type || 'MCQ'}
              </span>
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-8">{questions[currentIndex].text}</h2>
          <div className="space-y-3">
            {questions[currentIndex].options.map((opt: any) => (
              <button
                key={opt.id}
                onClick={() => handleAnswer(opt.id)}
                disabled={lastResult !== null}
                className={`w-full text-left p-4 rounded border transition ${
                  lastResult ? 'bg-gray-700 opacity-70' : 'bg-gray-700 hover:border-blue-500'
                }`}
              >
                {opt.text}
              </button>
            ))}
          </div>
          {lastResult && (
            <div
              className={`mt-6 p-4 rounded border ${
                lastResult.correct ? 'bg-green-900/30 border-green-500' : 'bg-red-900/30 border-red-500'
              }`}
            >
              <h3 className={`font-bold ${lastResult.correct ? 'text-green-400' : 'text-red-400'}`}>
                {lastResult.correct ? 'Correct!' : 'Incorrect'}
              </h3>
              <p className="text-sm mt-1 text-gray-300">{lastResult.explanation}</p>
              <button onClick={handleNext} className="mt-4 bg-gray-600 px-6 py-2 rounded hover:bg-gray-500 w-full">
                Next
              </button>
            </div>
          )}
        </div>
      )}

      {step === 'result' && questions.length > 0 && (
        <div className="bg-gray-800 p-10 rounded-xl text-center shadow-2xl">
          <h2 className="text-4xl font-bold text-white mb-4">Quiz Finished</h2>
          <div className="text-6xl font-extrabold text-blue-500 mb-2">{Math.round((score / questions.length) * 100)}%</div>
          <p className="text-gray-400 mb-6">
            Score: {score}/{questions.length} — Time: {formatTime(elapsedSeconds + 1)}
          </p>
          <div className="bg-gray-700 rounded p-4 text-left mb-6">
            <p className="text-sm text-gray-200">Final Performance Report</p>
            {generatedFromScan && (
              <p className="text-xs text-purple-200 mt-1">Based on your uploaded project vulnerabilities</p>
            )}
            <p className="text-xs text-gray-300 mt-1">Difficulty: {difficultyLevel}</p>
            <p className="text-xs text-gray-300 mt-1">Correct answers: {score}</p>
            <p className="text-xs text-gray-300 mt-1">Accuracy: {Math.round((score / questions.length) * 100)}%</p>
            <p className="text-xs text-gray-300 mt-1">
              Weak areas:{' '}
              {[...new Set((wrongCategories || []).filter(Boolean))].slice(0, 3).join(', ') || 'None detected'}
            </p>
            <p className="text-xs text-gray-300 mt-1">
              Recommendation:{' '}
              {Math.round((score / questions.length) * 100) >= 70
                ? 'Move to advanced mixed-vulnerability quizzes.'
                : 'Review explanations and retry weak categories.'}
            </p>
          </div>
          <button onClick={() => setStep('setup')} className="bg-gray-700 px-8 py-3 rounded font-bold hover:bg-gray-600">
            Back to Dashboard
          </button>
        </div>
      )}
    </div>
  );
};

export default StudentQuizPage;
