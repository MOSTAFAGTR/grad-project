import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaMagic } from 'react-icons/fa';
import { API_BASE_URL } from '../lib/api';

const API_URL = `${API_BASE_URL}/api`;

const InstructorQuizPage: React.FC = () => {
  const [tab, setTab] = useState('bank'); // bank, create, ai, assign, assign_list
  const [questions, setQuestions] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState({
    question: '',
    category: 'SQL Injection',
    difficulty: 'Easy',
    explanation: '',
    options: ['', '', '', ''],
    correct_answer: 0,
  });

  // Selection State for Assignment
  const [selectedQ, setSelectedQ] = useState<number[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [assignTitle, setAssignTitle] = useState('');

  // AI State
  const [aiParams, setAiParams] = useState({ topic: 'SQL Injection', count: 3, difficulty: 'Medium', skill_focus: 'Detection' });
  const [aiPreview, setAiPreview] = useState<any[]>([]);
  const [loadingAI, setLoadingAI] = useState(false);

  // Manual Question State
  const [newQ, setNewQ] = useState({
    question: '',
    options: ['', '', '', ''],
    correct_answer: 0,
    explanation: '',
    difficulty: 'Easy',
    category: 'SQL Injection',
  });

  const token = sessionStorage.getItem('token');
  const headers = { headers: { Authorization: `Bearer ${token}` } };

  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('Intermediate');
  const [numQuestions, setNumQuestions] = useState(10);
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);
  const [dueDate, setDueDate] = useState('');
  const [studentsLoading, setStudentsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateSuccess, setGenerateSuccess] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setStudentsLoading(true);
    try {
      const qRes = await axios.get(`${API_URL}/quizzes/manage`, headers);
      setQuestions(qRes.data.questions || []);
      const uRes = await axios.get(`${API_URL}/auth/users`, headers);
      setUsers(uRes.data);
      const aRes = await axios.get(`${API_URL}/quizzes/assignments/instructor`, headers);
      setAssignments(aRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setStudentsLoading(false);
    }
  };

  const studentUsers = users.filter((u: { role?: string }) => u.role === 'user');

  const handleAiGenerateAssign = async () => {
    setGenerateSuccess(null);
    setGenerateError(null);
    setIsGenerating(true);
    try {
      const res = await axios.post(
        `${API_URL}/quizzes/ai-generate-and-assign`,
        {
          topic: selectedTopic,
          difficulty: selectedDifficulty,
          num_questions: numQuestions,
          student_ids: selectedStudentIds,
          due_date: dueDate || null,
        },
        headers,
      );
      const d = res.data;
      let msg: string;
      if (d.ai_generated) {
        msg = `✓ AI-generated quiz assigned!\n${d.ai_questions_created} new questions were created by AI and added to the question bank.\nAssigned to ${d.students_assigned} student(s).`;
      } else {
        msg = `✓ Quiz assigned from question bank.\n(AI generation not available — questions selected from existing bank)\nAssigned to ${d.students_assigned} student(s).`;
      }
      if (d.mixed_topics) {
        msg +=
          '\n(Note: Topic had fewer questions than requested. Questions from other topics were included.)';
      }
      setGenerateSuccess(msg);
      setSelectedTopic('');
      setSelectedDifficulty('Intermediate');
      setNumQuestions(10);
      setSelectedStudentIds([]);
      setDueDate('');
      fetchData();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: unknown } } };
      const detail = ax.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((x: { msg?: string }) => x.msg || '').join(' ')
            : 'Request failed';
      setGenerateError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteQuestion = async (id: number) => {
    if (!confirm("Delete this question?")) return;
    await axios.post(`${API_URL}/quizzes/manage`, { action: 'delete', id }, headers);
    fetchData();
  };

  const startEditQuestion = (q: any) => {
    setEditingId(q.id);
    setEditDraft({
      question: q.question || '',
      category: q.category || 'SQL Injection',
      difficulty: q.difficulty || 'Easy',
      explanation: q.explanation || '',
      options: Array.isArray(q.options) && q.options.length === 4 ? q.options : ['', '', '', ''],
      correct_answer: Number.isInteger(q.correct_answer) ? q.correct_answer : 0,
    });
  };

  const saveEditQuestion = async () => {
    if (!editingId) return;
    await axios.post(
      `${API_URL}/quizzes/manage`,
      { action: 'update', id: editingId, ...editDraft },
      headers
    );
    setEditingId(null);
    fetchData();
  };

  const handleDeleteAllQuestions = async () => {
    if (!confirm("Are you sure you want to delete ALL questions from the bank? This cannot be undone.")) return;
    try {
      await Promise.all(
        questions.map((q) => axios.post(`${API_URL}/quizzes/manage`, { action: 'delete', id: q.id }, headers))
      );
      fetchData();
    } catch (err) { alert("Failed to delete all questions"); }
  };


  const handleCreateAssignment = async () => {
    if (selectedQ.length === 0 || selectedUsers.length === 0 || !assignTitle) {
      alert("Please select questions, users, and a title.");
      return;
    }
    await axios.post(`${API_URL}/quizzes/assignments`, {
      title: assignTitle,
      student_ids: selectedUsers,
      question_ids: selectedQ
    }, headers);
    alert("Assignment Sent!");
    fetchData();
    setTab('assign_list');
  };

  const handleDeleteAssignment = async (id: number) => {
    await axios.delete(`${API_URL}/quizzes/assignments/${id}`, headers);
    fetchData();
  };

  // --- AI HANDLERS ---
  const handleGenerateAI = async () => {
    setLoadingAI(true);
    try {
      const res = await axios.post(`${API_URL}/quizzes/generate-ai-preview`, aiParams, headers);
      setAiPreview(Array.isArray(res.data) ? res.data : []);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: unknown } } };
      const d = ax.response?.data?.detail;
      const msg =
        typeof d === 'string'
          ? d
          : 'Could not generate preview. Check SERPER_API_KEY or OPENAI_API_KEY, or try again.';
      alert(msg);
      setAiPreview([]);
    } finally {
      setLoadingAI(false);
    }
  };

  const saveQuestionToBank = async (q: any) => {
    const normalizedOptions = Array.isArray(q.options)
      ? q.options.map((o: any) => (typeof o === 'string' ? o : o?.text || '')).slice(0, 4)
      : [];
    while (normalizedOptions.length < 4) normalizedOptions.push('');
    const payload = {
      action: 'create',
      question: q.question || q.text || '',
      options: normalizedOptions,
      correct_answer: Number.isInteger(q.correct_answer) ? q.correct_answer : 0,
      explanation: q.explanation || '',
      difficulty: q.difficulty || 'Easy',
      category: q.category || q.topic || 'General',
    };
    await axios.post(`${API_URL}/quizzes/manage`, payload, headers);
    alert("Saved!");
    fetchData();
  };

  // --- MANUAL HANDLERS ---
  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQ.explanation.trim()) {
      alert('Explanation is required');
      return;
    }
    await saveQuestionToBank(newQ);
    setNewQ({ ...newQ, question: '', options: ['', '', '', ''], correct_answer: 0, explanation: '' });
  };

  const handleOptionChange = (idx: number, val: string) => {
    const updatedOptions = [...newQ.options];
    updatedOptions[idx] = val;
    setNewQ({ ...newQ, options: updatedOptions });
  };

  // Toggle helpers
  const toggleQ = (id: number) => {
    setSelectedQ(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };
  const toggleU = (id: number) => {
    setSelectedUsers(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const topicOptions = [
    { value: '', label: 'Select a topic...', disabled: true },
    { value: 'SQL Injection', label: 'SQL Injection' },
    { value: 'XSS', label: 'XSS' },
    { value: 'CSRF', label: 'CSRF' },
    { value: 'Command Injection', label: 'Command Injection' },
    { value: 'Broken Authentication', label: 'Broken Authentication' },
    { value: 'Security Misconfiguration', label: 'Security Misconfiguration' },
    { value: 'Insecure Storage', label: 'Insecure Storage' },
    { value: 'Directory Traversal', label: 'Directory Traversal' },
    { value: 'XXE', label: 'XXE' },
    { value: 'Unvalidated Redirect', label: 'Unvalidated Redirect' },
    { value: 'Mixed (All Topics)', label: 'Mixed (All Topics)' },
  ];

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <h1 className="text-3xl font-bold mb-6 text-purple-400">Admin Quiz Dashboard</h1>

      <div className="flex flex-wrap gap-4 mb-6 border-b border-gray-700 pb-2">
        <button onClick={() => setTab('bank')} className={`px-4 py-2 rounded ${tab === 'bank' ? 'bg-blue-600' : 'bg-gray-800'}`}>Question Bank</button>
        <button onClick={() => setTab('create')} className={`px-4 py-2 rounded ${tab === 'create' ? 'bg-blue-600' : 'bg-gray-800'}`}>+ Add Question</button>
        <button
          onClick={() => setTab('ai')}
          className={`px-4 py-2 rounded inline-flex items-center gap-2 ${tab === 'ai' ? 'bg-purple-600' : 'bg-gray-800'}`}
        >
          <FaMagic /> AI Generator
        </button>
        <button onClick={() => setTab('assign')} className={`px-4 py-2 rounded ${tab === 'assign' ? 'bg-green-600' : 'bg-gray-800'}`}>Assign Quiz</button>
        <button onClick={() => setTab('assign_list')} className={`px-4 py-2 rounded ${tab === 'assign_list' ? 'bg-gray-700' : 'bg-gray-800'}`}>History</button>
      </div>

      {/* --- BANK TAB --- */}
      {tab === 'bank' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Total Questions: {questions.length}</h2>
            {questions.length > 0 && (
              <button
                onClick={handleDeleteAllQuestions}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-bold transition-colors"
              >
                Delete All Questions
              </button>
            )}
          </div>
          {questions.map(q => (
            <div key={q.id} className="bg-gray-800 p-4 rounded flex justify-between items-center border border-gray-700">
              {editingId === q.id ? (
                <div className="w-full space-y-2">
                  <input className="w-full bg-gray-700 p-2 rounded text-white" value={editDraft.question} onChange={(e) => setEditDraft({ ...editDraft, question: e.target.value })} />
                  <div className="flex gap-2">
                    <select className="w-1/2 bg-gray-700 p-2 rounded text-white" value={editDraft.category} onChange={(e) => setEditDraft({ ...editDraft, category: e.target.value })}>
                      <option>SQL Injection</option><option>XSS</option><option>CSRF</option><option>Command Injection</option><option>Authentication</option><option>General</option>
                    </select>
                    <select className="bg-gray-700 p-2 rounded text-white" value={editDraft.difficulty} onChange={(e) => setEditDraft({ ...editDraft, difficulty: e.target.value })}>
                      <option>Easy</option><option>Medium</option><option>Hard</option>
                    </select>
                  </div>
                  {editDraft.options.map((opt, idx) => (
                    <input
                      key={idx}
                      className="w-full bg-gray-700 p-2 rounded text-white"
                      value={opt}
                      onChange={(e) => {
                        const options = [...editDraft.options];
                        options[idx] = e.target.value;
                        setEditDraft({ ...editDraft, options });
                      }}
                      placeholder={`Option ${idx + 1}`}
                    />
                  ))}
                  <select className="bg-gray-700 p-2 rounded text-white" value={editDraft.correct_answer} onChange={(e) => setEditDraft({ ...editDraft, correct_answer: Number(e.target.value) })}>
                    <option value={0}>Correct: Option 1</option><option value={1}>Correct: Option 2</option><option value={2}>Correct: Option 3</option><option value={3}>Correct: Option 4</option>
                  </select>
                  <textarea className="w-full bg-gray-700 p-2 rounded text-white h-20" value={editDraft.explanation} onChange={(e) => setEditDraft({ ...editDraft, explanation: e.target.value })} />
                  <div className="flex gap-3">
                    <button onClick={saveEditQuestion} className="text-green-400 hover:underline">Save</button>
                    <button onClick={() => setEditingId(null)} className="text-gray-300 hover:underline">Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <div>
                    <p className="font-bold">{q.question}</p>
                    <span className="text-xs text-gray-400">{q.difficulty} | {q.category}</span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => startEditQuestion(q)} className="text-blue-400 hover:underline">Edit</button>
                    <button onClick={() => handleDeleteQuestion(q.id)} className="text-red-400 hover:underline">Delete</button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {/* --- MANUAL ADD TAB --- */}
      {tab === 'create' && (
        <form onSubmit={handleManualSubmit} className="bg-gray-800 p-6 rounded space-y-4 max-w-2xl">
          <h3 className="text-xl font-bold">Add New Question</h3>
          <input className="w-full bg-gray-700 p-2 rounded text-white" placeholder="Question Text" value={newQ.question} onChange={e => setNewQ({ ...newQ, question: e.target.value })} required />
          <div className="flex gap-2">
            <select className="w-1/2 bg-gray-700 p-2 rounded text-white" value={newQ.category} onChange={e => setNewQ({ ...newQ, category: e.target.value })}>
              <option>SQL Injection</option><option>XSS</option><option>CSRF</option><option>Command Injection</option><option>Authentication</option><option>General</option>
            </select>
            <select className="bg-gray-700 p-2 rounded text-white" value={newQ.difficulty} onChange={e => setNewQ({ ...newQ, difficulty: e.target.value })}>
              <option>Easy</option><option>Medium</option><option>Hard</option>
            </select>
          </div>
          <textarea className="w-full bg-gray-700 p-2 rounded text-white h-20" placeholder="Explanation (required)" value={newQ.explanation} onChange={e => setNewQ({ ...newQ, explanation: e.target.value })} required />

          <div className="space-y-2">
            <label>Options (4 required):</label>
            {newQ.options.map((opt, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <input className="flex-1 bg-gray-700 p-2 rounded text-white" placeholder={`Option ${idx + 1}`} value={opt} onChange={e => handleOptionChange(idx, e.target.value)} required />
              </div>
            ))}
            <select className="bg-gray-700 p-2 rounded text-white" value={newQ.correct_answer} onChange={e => setNewQ({ ...newQ, correct_answer: Number(e.target.value) })}>
              <option value={0}>Correct: Option 1</option><option value={1}>Correct: Option 2</option><option value={2}>Correct: Option 3</option><option value={3}>Correct: Option 4</option>
            </select>
          </div>
          <button type="submit" className="bg-green-600 px-6 py-2 rounded font-bold w-full">Save to Bank</button>
        </form>
      )}

      {/* --- AI GENERATOR TAB --- */}
      {tab === 'ai' && (
        <div className="space-y-6">
          <section className="border border-gray-700 rounded-xl p-6 bg-gray-800/40">
            <h2 className="text-2xl font-bold text-cyan-400 mb-1">Generate and Assign AI Quiz</h2>
            <p className="text-gray-400 text-sm mb-6">
              Create a targeted quiz from the question bank (with optional AI-generated questions) and assign it to
              students in one step.
            </p>

            <div className="space-y-4 max-w-2xl">
              <div>
                <label className="block text-gray-300 text-sm mb-1">Vulnerability Topic</label>
                <select
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 text-white"
                  value={selectedTopic}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                >
                  {topicOptions.map((o) => (
                    <option key={o.label} value={o.value} disabled={o.disabled}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <span className="block text-gray-300 text-sm mb-2">Difficulty Level</span>
                <div className="flex flex-wrap gap-2">
                  {(['Beginner', 'Intermediate', 'Advanced'] as const).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setSelectedDifficulty(d)}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold border ${
                        selectedDifficulty === d
                          ? 'bg-purple-600 border-purple-500 text-white'
                          : 'bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-1">Number of questions</label>
                <input
                  type="number"
                  min={5}
                  max={20}
                  step={1}
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(Number(e.target.value))}
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 text-white"
                />
                <p className="text-xs text-gray-500 mt-1">5–20 questions</p>
              </div>

              <div>
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <label className="block text-gray-300 text-sm">Assign to students</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600"
                      onClick={() => setSelectedStudentIds(studentUsers.map((u: { id: number }) => u.id))}
                    >
                      Select All
                    </button>
                    <button
                      type="button"
                      className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600"
                      onClick={() => setSelectedStudentIds([])}
                    >
                      Clear All
                    </button>
                  </div>
                </div>
                <div className="max-h-[200px] overflow-y-auto border border-gray-600 rounded p-2 bg-gray-800/80 space-y-2">
                  {studentsLoading ? (
                    <p className="text-gray-500 text-sm">Loading students…</p>
                  ) : (
                    studentUsers.map((u: { id: number; email: string }) => (
                      <label key={u.id} className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedStudentIds.includes(u.id)}
                          onChange={() =>
                            setSelectedStudentIds((prev) =>
                              prev.includes(u.id) ? prev.filter((x) => x !== u.id) : [...prev, u.id],
                            )
                          }
                        />
                        <span>{u.email}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-1">Due date (optional)</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 text-white"
                />
                <p className="text-xs text-gray-500 mt-1">Leave blank for no deadline</p>
              </div>

              <button
                type="button"
                disabled={!selectedTopic || selectedStudentIds.length === 0 || isGenerating}
                onClick={handleAiGenerateAssign}
                className="w-full py-3 rounded-lg font-bold bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white"
              >
                {isGenerating ? 'Generating...' : 'Generate and Assign Quiz'}
              </button>
            </div>

            {generateSuccess && (
              <div className="mt-4 p-4 rounded-lg bg-emerald-900/40 border border-emerald-600 text-emerald-100 whitespace-pre-line text-sm">
                {generateSuccess}
              </div>
            )}
            {generateError && (
              <div className="mt-4 p-4 rounded-lg bg-red-900/40 border border-red-600 text-red-100 text-sm">
                {generateError}
              </div>
            )}
          </section>

          <div className="bg-gray-800 p-6 rounded border border-purple-900">
            <h2 className="text-xl font-bold mb-4 text-purple-400">AI Question Generator</h2>
            <div className="grid grid-cols-2 gap-4">
              <input className="bg-gray-700 p-2 rounded text-white" placeholder="Topic" value={aiParams.topic} onChange={e => setAiParams({ ...aiParams, topic: e.target.value })} />
              <input type="number" className="bg-gray-700 p-2 rounded text-white" value={aiParams.count} onChange={e => setAiParams({ ...aiParams, count: parseInt(e.target.value) })} min="1" max="10" />
            </div>
            <button onClick={handleGenerateAI} disabled={loadingAI} className="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 rounded">
              {loadingAI ? "Generating..." : "Generate Preview"}
            </button>
          </div>
          <div className="space-y-4">
            {aiPreview.map((q, i) => (
              <div key={i} className="bg-gray-800 p-4 rounded border border-gray-600 flex justify-between items-start">
                <div>
                  <p className="font-bold text-lg">{q.text}</p>
                  <p className="text-sm text-gray-400">Answer: {q.explanation}</p>
                </div>
                <button onClick={() => saveQuestionToBank(q)} className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm">Save</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- CREATE ASSIGNMENT TAB --- */}
      {tab === 'assign' && (
        <div className="grid grid-cols-2 gap-6">
          {/* Left: Questions */}
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-xl font-bold mb-4">1. Select Questions</h3>
            <div className="h-64 overflow-y-auto space-y-2">
              {questions.map(q => (
                <div key={q.id} onClick={() => toggleQ(q.id)}
                  className={`p-2 rounded cursor-pointer ${selectedQ.includes(q.id) ? 'bg-green-900 border-green-500 border' : 'bg-gray-700'}`}>
                  {q.question}
                </div>
              ))}
            </div>
          </div>

          {/* Right: Users */}
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-xl font-bold mb-4">2. Select Students</h3>
            <div className="h-64 overflow-y-auto space-y-2">
              {users.map(u => (
                <div key={u.id} onClick={() => toggleU(u.id)}
                  className={`p-2 rounded cursor-pointer ${selectedUsers.includes(u.id) ? 'bg-blue-900 border-blue-500 border' : 'bg-gray-700'}`}>
                  {u.email} ({u.role})
                </div>
              ))}
            </div>
          </div>

          {/* Bottom: Submit */}
          <div className="col-span-2">
            <input
              className="w-full bg-gray-700 p-3 rounded mb-4 text-white"
              placeholder="Assignment Title (e.g. Midterm SQLi Exam)"
              value={assignTitle} onChange={e => setAssignTitle(e.target.value)}
            />
            <button onClick={handleCreateAssignment} className="w-full bg-green-600 py-3 rounded font-bold hover:bg-green-700">
              Send Assignment ({selectedQ.length} Qs to {selectedUsers.length} Students)
            </button>
          </div>
        </div>
      )}

      {/* --- ASSIGNMENT HISTORY TAB --- */}
      {tab === 'assign_list' && (
        <div className="space-y-4">
          {assignments.map(a => (
            <div key={a.id} className="bg-gray-800 p-4 rounded flex justify-between border border-gray-700">
              <div>
                <h3 className="font-bold text-lg">{a.title}</h3>
                <p className="text-sm text-gray-400">Created: {new Date(a.created_at).toLocaleDateString()}</p>
              </div>
              <button onClick={() => handleDeleteAssignment(a.id)} className="bg-red-600 px-3 py-1 rounded text-sm hover:bg-red-700">Delete</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default InstructorQuizPage;