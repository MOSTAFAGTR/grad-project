import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../lib/api';
import { DEFAULT_PAYLOADS, getDefaultPayload } from '../utils/payloads';

type AttackSimResponse = {
  original_state: string;
  payload: string;
  injected_state: string;
  execution_flow: string;
  result: string;
  data_exposed: string;
  impact: string;
  timeline: string[];
};

type AttackLabState = {
  vulnerability_type?: string;
  code?: string;
  payload?: string;
};

const AttackLab: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = (location.state || {}) as AttackLabState;
  const hasIncomingState = Boolean(state.vulnerability_type);
  const vulnerabilityType = state.vulnerability_type || 'Unknown';

  const [code, setCode] = useState<string>(state.code || '');
  const [payload, setPayload] = useState<string>(
    state.payload || getDefaultPayload(vulnerabilityType) || '',
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AttackSimResponse | null>(null);
  const [visibleStep, setVisibleStep] = useState(0);
  const [isReplaying, setIsReplaying] = useState(false);

  const timelineToShow = useMemo(() => {
    if (!result?.timeline) return [];
    return result.timeline.slice(0, visibleStep);
  }, [result, visibleStep]);

  const runSimulation = async () => {
    const effectivePayload = payload || getDefaultPayload(vulnerabilityType) || DEFAULT_PAYLOADS['SQL Injection'];
    if (!payload) setPayload(effectivePayload);
    setLoading(true);
    setError('');
    setResult(null);
    setVisibleStep(0);
    try {
      const response = await fetch(`${API_BASE_URL}/api/attack/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${sessionStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify({
          vulnerability_type: vulnerabilityType,
          code,
          payload: effectivePayload,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Attack simulation failed');
      }
      const data: AttackSimResponse = await response.json();
      setResult(data);
      setVisibleStep(data.timeline?.length || 0);
    } catch (e: any) {
      setError(e.message || 'Attack simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const replayAttack = async () => {
    if (!result?.timeline?.length || isReplaying) return;
    setIsReplaying(true);
    setVisibleStep(0);
    for (let i = 1; i <= result.timeline.length; i += 1) {
      // Sequential reveal animation
      await new Promise((resolve) => setTimeout(resolve, 600));
      setVisibleStep(i);
    }
    setIsReplaying(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-mono">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-green-400">Attack Simulation Lab</h1>
          <button
            onClick={() => navigate('/scanner')}
            className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 text-sm"
          >
            Back to Scanner
          </button>
        </div>

        {!hasIncomingState && (
          <div className="bg-amber-900/40 border border-amber-700 rounded p-3 text-sm text-amber-200">
            No attack data provided. Please simulate from scanner.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-lg text-cyan-300 font-bold mb-3">Request Panel</h2>
            <label className="text-xs text-gray-400">Vulnerability Type</label>
            <div className="w-full mt-1 mb-3 p-2 bg-gray-950 border border-cyan-700 text-cyan-200 rounded">
              {vulnerabilityType}
            </div>
            <label className="text-xs text-gray-400">Vulnerable Code</label>
            <textarea
              className="w-full mt-1 h-40 p-2 bg-black border border-gray-700 rounded text-green-300"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </section>

          <section className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-lg text-red-300 font-bold mb-3">Payload Panel</h2>
            <label className="text-xs text-gray-400">Attack Payload</label>
            <textarea
              className="w-full mt-1 h-40 p-2 bg-black border border-red-800 rounded text-red-300"
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              placeholder={getDefaultPayload(vulnerabilityType) || 'Enter payload'}
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={runSimulation}
                disabled={loading}
                className="px-4 py-2 rounded bg-red-700 hover:bg-red-600 disabled:opacity-50 text-sm font-bold"
              >
                {loading ? 'Simulating...' : 'Run Attack Simulation'}
              </button>
              <button
                onClick={replayAttack}
                disabled={!result || isReplaying}
                className="px-4 py-2 rounded bg-yellow-700 hover:bg-yellow-600 disabled:opacity-50 text-sm font-bold"
              >
                {isReplaying ? 'Replaying...' : '▶ Replay Attack'}
              </button>
            </div>
          </section>
        </div>

        {error && (
          <div className="bg-red-900/40 border border-red-700 rounded p-3 text-sm text-red-200">{error}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-lg text-purple-300 font-bold mb-3">Execution Panel</h2>
            {!result && <p className="text-sm text-gray-400">Run a simulation to visualize execution flow.</p>}
            {result && (
              <div className="space-y-3">
                <p className="text-sm text-gray-200 whitespace-pre-wrap">{result.execution_flow}</p>
                <div className="space-y-2">
                  {timelineToShow.map((step, idx) => (
                    <div key={idx} className="bg-gray-950 border border-gray-700 rounded p-2 text-sm">
                      <span className="text-purple-300 font-bold">Step {idx + 1}:</span> {step}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-lg text-green-300 font-bold mb-3">Result Panel</h2>
            {!result && <p className="text-sm text-gray-400">Simulation output will appear here.</p>}
            {result && (
              <div className="space-y-3 text-sm">
                <div className="bg-gray-950 border border-gray-700 rounded p-2">
                  <div className="text-gray-400 text-xs mb-1">Original State</div>
                  <pre className="whitespace-pre-wrap text-cyan-200">{result.original_state}</pre>
                </div>
                <div className="bg-gray-950 border border-red-800 rounded p-2">
                  <div className="text-red-300 text-xs mb-1">Injected State</div>
                  <pre className="whitespace-pre-wrap text-red-200">{result.injected_state}</pre>
                </div>
                <div className="bg-gray-950 border border-gray-700 rounded p-2">
                  <div className="text-gray-400 text-xs mb-1">Result</div>
                  <p className="text-yellow-200">{result.result}</p>
                </div>
                <div className="bg-gray-950 border border-gray-700 rounded p-2">
                  <div className="text-gray-400 text-xs mb-1">Data Exposed</div>
                  <p>{result.data_exposed}</p>
                </div>
                <div className="bg-gray-950 border border-gray-700 rounded p-2">
                  <div className="text-gray-400 text-xs mb-1">Impact</div>
                  <p className="text-orange-200">{result.impact}</p>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default AttackLab;

