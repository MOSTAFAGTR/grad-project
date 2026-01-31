import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const InstructorQuizPage: React.FC = () => {
  const [tab, setTab] = useState('bank'); // bank, create, ai, assign, assign_list
  const [questions, setQuestions] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);

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
    text: '', type: 'MCQ', topic: 'SQL Injection', difficulty: 'Easy', skill_focus: 'Concepts', explanation: '',
    options: [{ text: '', is_correct: false }, { text: '', is_correct: false }]
  });

  const token = sessionStorage.getItem('token');
  const headers = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const qRes = await axios.get(`${API_URL}/quizzes/questions`, headers);
      setQuestions(qRes.data);
      const uRes = await axios.get(`${API_URL}/auth/users`, headers);
      setUsers(uRes.data);
      const aRes = await axios.get(`${API_URL}/quizzes/assignments/instructor`, headers);
      setAssignments(aRes.data);
    } catch (err) { console.error(err); }
  };

  const handleDeleteQuestion = async (id: number) => {
    if (!confirm("Delete this question?")) return;
    await axios.delete(`${API_URL}/quizzes/questions/${id}`, headers);
    fetchData();
  };

  const handleDeleteAllQuestions = async () => {
    if (!confirm("Are you sure you want to delete ALL questions from the bank? This cannot be undone.")) return;
    try {
      await axios.delete(`${API_URL}/quizzes/questions`, headers);
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
      setAiPreview(res.data);
    } catch (err) { alert("AI Service Failed"); }
    setLoadingAI(false);
  };

  const saveQuestionToBank = async (q: any) => {
    await axios.post(`${API_URL}/quizzes/questions`, q, headers);
    alert("Saved!");
    fetchData();
  };

  // --- MANUAL HANDLERS ---
  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await saveQuestionToBank(newQ);
    setNewQ({ ...newQ, text: '' });
  };

  const handleOptionChange = (idx: number, field: string, val: any) => {
    const updatedOptions: any = [...newQ.options];
    updatedOptions[idx][field] = val;
    setNewQ({ ...newQ, options: updatedOptions });
  };

  const addOption = () => setNewQ({ ...newQ, options: [...newQ.options, { text: '', is_correct: false }] });

  // Toggle helpers
  const toggleQ = (id: number) => {
    setSelectedQ(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };
  const toggleU = (id: number) => {
    setSelectedUsers(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <h1 className="text-3xl font-bold mb-6 text-purple-400">Admin Quiz Dashboard</h1>

      <div className="flex flex-wrap gap-4 mb-6 border-b border-gray-700 pb-2">
        <button onClick={() => setTab('bank')} className={`px-4 py-2 rounded ${tab === 'bank' ? 'bg-blue-600' : 'bg-gray-800'}`}>Question Bank</button>
        <button onClick={() => setTab('create')} className={`px-4 py-2 rounded ${tab === 'create' ? 'bg-blue-600' : 'bg-gray-800'}`}>+ Add Question</button>
        <button onClick={() => setTab('ai')} className={`px-4 py-2 rounded ${tab === 'ai' ? 'bg-purple-600' : 'bg-gray-800'}`}>AI Generator</button>
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
              <div>
                <p className="font-bold">{q.text}</p>
                <span className="text-xs text-gray-400">{q.difficulty} | {q.topic}</span>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleDeleteQuestion(q.id)} className="text-red-400 hover:underline">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- MANUAL ADD TAB --- */}
      {tab === 'create' && (
        <form onSubmit={handleManualSubmit} className="bg-gray-800 p-6 rounded space-y-4 max-w-2xl">
          <h3 className="text-xl font-bold">Add New Question</h3>
          <input className="w-full bg-gray-700 p-2 rounded text-white" placeholder="Question Text" value={newQ.text} onChange={e => setNewQ({ ...newQ, text: e.target.value })} required />
          <div className="flex gap-2">
            <input className="w-1/2 bg-gray-700 p-2 rounded text-white" placeholder="Topic" value={newQ.topic} onChange={e => setNewQ({ ...newQ, topic: e.target.value })} />
            <select className="bg-gray-700 p-2 rounded text-white" value={newQ.difficulty} onChange={e => setNewQ({ ...newQ, difficulty: e.target.value })}>
              <option>Easy</option><option>Medium</option><option>Hard</option>
            </select>
          </div>
          <textarea className="w-full bg-gray-700 p-2 rounded text-white h-20" placeholder="Explanation" value={newQ.explanation} onChange={e => setNewQ({ ...newQ, explanation: e.target.value })} />

          <div className="space-y-2">
            <label>Options:</label>
            {newQ.options.map((opt, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <input type="checkbox" checked={opt.is_correct} onChange={e => handleOptionChange(idx, 'is_correct', e.target.checked)} />
                <input className="flex-1 bg-gray-700 p-2 rounded text-white" placeholder={`Option ${idx + 1}`} value={opt.text} onChange={e => handleOptionChange(idx, 'text', e.target.value)} required />
              </div>
            ))}
            <button type="button" onClick={addOption} className="text-sm text-blue-400 hover:underline">+ Add Option</button>
          </div>
          <button type="submit" className="bg-green-600 px-6 py-2 rounded font-bold w-full">Save to Bank</button>
        </form>
      )}

      {/* --- AI GENERATOR TAB --- */}
      {tab === 'ai' && (
        <div className="space-y-6">
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
                  {q.text}
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