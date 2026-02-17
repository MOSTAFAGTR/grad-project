import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';

const VULNERABLE_CODE = `import sqlite3
from flask import Flask, request, jsonify, session
import secrets

app = Flask(__name__)
app.secret_key = 'secret'

# In-Memory DB setup (Hidden for brevity)
def get_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE accounts (username TEXT, balance INT)')
    c.execute("INSERT INTO accounts VALUES ('Alice', 1000)")
    c.execute("INSERT INTO accounts VALUES ('Bob', 0)")
    conn.commit()
    return conn
    
db_conn = get_db()

@app.route('/form', methods=['GET'])
def transfer_form():
    # TODO: 1. Generate a random token
    # TODO: 2. Store it in the session
    # TODO: 3. Return it in the JSON
    return jsonify({"message": "Form loaded", "csrf_token": "TODO"})

@app.route('/transfer', methods=['POST'])
def transfer():
    current_user = 'Alice'
    to_user = request.form.get('to_user')
    amount = int(request.form.get('amount'))
    
    # TODO: 4. Get the token from the request form
    # TODO: 5. Compare it with the token in the session
    #If they don't match, return 403 error
    
    # ... Transfer Logic ...
    cursor = db_conn.cursor()
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE username=?", (amount, current_user))
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE username=?", (amount, to_user))
    db_conn.commit()
    
    return jsonify({"message": "Transfer successful"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
`;

const CsrfFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      if (!token) { alert("Please login."); setIsLoading(false); return; }

      const response = await axios.post(
        'http://localhost:8000/api/challenges/submit-fix-csrf', 
        { code }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setModalState({
        isOpen: true,
        isSuccess: response.data.success,
        logs: response.data.logs
      });

    } catch (error: any) {
      setModalState({
        isOpen: true,
        isSuccess: false,
        logs: error.response?.data?.detail || "System Error"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-4">CSRF: Fix Challenge</h1>
      <p className="text-gray-400 mb-4">
        Implement a CSRF Token pattern. 
        1. Generate a token in <code>/form</code>. 
        2. Validate it in <code>/transfer</code>.
      </p>
      
      <div className="flex-grow mb-4 border-2 border-gray-700 rounded-lg overflow-hidden">
        <Editor height="60vh" language="python" theme="vs-dark" value={code} onChange={(v) => setCode(v || '')} />
      </div>

      <button onClick={handleSubmit} disabled={isLoading} className="bg-green-600 w-48 py-3 rounded font-bold hover:bg-green-700 transition flex justify-center items-center gap-2">
        {isLoading ? <span className="animate-spin">↻</span> : 'Submit Fix'}
      </button>

      <ResultModal 
        isOpen={modalState.isOpen} 
        isSuccess={modalState.isSuccess} 
        logs={modalState.logs} 
        onClose={() => setModalState({ ...modalState, isOpen: false })} 
      />
    </div>
  );
};

export default CsrfFixPage;