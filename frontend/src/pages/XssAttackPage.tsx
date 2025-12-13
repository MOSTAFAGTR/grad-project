import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';

interface Comment {
  id: number;
  author: string;
  content: string;
}

const XssAttackPage: React.FC = () => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [author, setAuthor] = useState('Guest');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const fetchComments = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/challenges/xss/comments');
      setComments(res.data);
    } catch (err) {
      console.error("Failed to load comments");
    }
  };

  useEffect(() => {
    fetchComments();
  }, []);

  const handlePost = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/api/challenges/xss/comments', {
        author: author,
        content: newComment
      });
      setNewComment('');
      await fetchComments();
      setMessage('Comment posted!');
      // Check if the comment contains XSS payload and navigate after render
      if (newComment.toLowerCase().includes('<script') ||
        newComment.toLowerCase().includes('onerror') ||
        newComment.toLowerCase().includes('javascript:')) {
        setTimeout(() => navigate('/challenges/attack-success?type=xss'), 100);
      }
    } catch (err) {
      setMessage('Error posting comment.');
    }
  }; const handleClear = async () => {
    await axios.delete('http://localhost:8000/api/challenges/xss/comments');
    fetchComments();
  };

  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Reflected/Stored XSS Challenge</h1>
      <p className="text-gray-400 mb-6">
        This blog post has no security. If you post a script tag, it will execute in the browser of anyone who visits this page.
      </p>

      {/* Fake Blog Post */}
      <div className="bg-gray-800 p-6 rounded-lg mb-8 border border-gray-700">
        <h2 className="text-2xl font-bold text-blue-400">Welcome to the Community!</h2>
        <p className="mt-2 text-gray-300">
          We are excited to announce the launch of our new platform. Please leave your feedback below!
        </p>
      </div>

      {/* Comment Form */}
      <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 mb-8">
        <h3 className="text-xl font-bold mb-4">Leave a Comment</h3>
        <form onSubmit={handlePost}>
          <div className="mb-4">
            <label className="block text-sm font-bold mb-2">Name</label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="bg-gray-700 border border-gray-600 text-white rounded w-full p-2"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-bold mb-2">Comment (Try: <code>&lt;img src=x onerror=alert(1)&gt;</code>)</label>
            <textarea
              className="bg-gray-700 border border-gray-600 text-white rounded w-full p-2 h-24"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Enter your message..."
            />
          </div>
          <div className="flex justify-between items-center">
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold">
              Post Comment
            </button>
            <button type="button" onClick={handleClear} className="text-red-400 hover:text-red-300 text-sm">
              Reset/Clear All Comments
            </button>
          </div>
        </form>
        {message && <p className="mt-2 text-sm text-green-400">{message}</p>}
      </div>

      {/* Vulnerable Comments Section */}
      <div className="space-y-4">
        <h3 className="text-2xl font-bold">Comments ({comments.length})</h3>
        {comments.map((c) => (
          <div key={c.id} className="bg-gray-800 p-4 rounded border border-gray-700">
            <div className="font-bold text-blue-300 text-sm mb-1">{c.author} says:</div>

            {/* VULNERABLE PART: RENDER HTML DIRECTLY */}
            <div
              className="text-gray-200"
              dangerouslySetInnerHTML={{ __html: c.content }}
            />
          </div>
        ))}
      </div>

      <div className="mt-8">
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
          Back to Challenges
        </Link>
      </div>
    </div>
  );
};

export default XssAttackPage;
