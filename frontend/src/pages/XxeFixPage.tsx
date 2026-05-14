import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import ChallengeHintPanel from '../components/ChallengeHintPanel';
import { API_BASE_URL } from '../lib/api';

const VULNERABLE_CODE = `import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/parse", methods=["POST"])
def parse_xml():
    payload = request.get_json(silent=True) or {}
    xml_input = payload.get("xml", "")
    if not xml_input:
        return jsonify({"error": "xml is required"}), 400

    # VULNERABLE: external entities are treated as resolved.
    if "<!ENTITY" in xml_input.upper():
        return jsonify({
            "parsed_output": "root:x:0:0:/root:/bin/bash",
            "sensitive_data": "/etc/passwd content",
            "attack_success": True
        }), 200

    parsed = ET.fromstring(xml_input)
    return jsonify({"parsed_output": ET.tostring(parsed, encoding="unicode"), "attack_success": False}), 200
`;

const XxeFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({
    isOpen: false,
    isSuccess: false,
    logs: '',
    verification: null as null | { before_vulnerabilities?: number; after_vulnerabilities?: number; improvement_score?: number },
  });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      const response = await axios.post(
        `${API_BASE_URL}/api/challenges/submit-fix-xxe`,
        { code },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setModalState({
        isOpen: true,
        isSuccess: response.data.success,
        logs: response.data.logs,
        verification: {
          before_vulnerabilities: response.data.before_vulnerabilities,
          after_vulnerabilities: response.data.after_vulnerabilities,
          improvement_score: response.data.improvement_score,
        },
      });
    } catch (error: any) {
      setModalState({
        isOpen: true,
        isSuccess: false,
        logs: error.response?.data?.detail || 'System Error',
        verification: null,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">XXE: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">Disable external entity handling and keep normal XML parsing functional.</p>
      <div className="h-96 mb-6 border-2 border-gray-700 rounded-lg overflow-hidden shadow-lg">
        <Editor height="100%" language="python" theme="vs-dark" value={code} onChange={(v) => setCode(v || '')} />
      </div>
      <button onClick={handleSubmit} disabled={isLoading} className="bg-green-600 px-8 py-3 rounded font-bold hover:bg-green-700 transition disabled:opacity-50">
        {isLoading ? 'Running Tests...' : 'Submit Fix'}
      </button>
      <div className="mt-6">
        <ChallengeHintPanel challengeId="xxe" />
      </div>
      <ResultModal
        isOpen={modalState.isOpen}
        isSuccess={modalState.isSuccess}
        logs={modalState.logs}
        verification={modalState.verification}
        onClose={() => setModalState({ ...modalState, isOpen: false })}
      />
    </div>
  );
};

export default XxeFixPage;
