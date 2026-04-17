import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { api } from '../lib/api';

interface Step {
  step: number;
  type: string;
  title: string;
  description: string;
  data: string | null;
}

interface Props {
  challengeSlug: string;
  isSample?: boolean;
  onClose: () => void;
}

function formatSlug(slug: string): string {
  return slug
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function renderHttpData(data: string): React.ReactNode {
  let html = data
    .replace(/^(GET|POST|PUT|DELETE|PATCH)\b/gm, '<span style="color:#4fc1ff">$1</span>')
    .replace(/(\/[a-zA-Z0-9_\-/?&=.:]+)/g, '<span style="color:#ffffff">$1</span>');
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

function renderSqlData(data: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const kw = /(SELECT|UPDATE|INSERT|DELETE)\b/gi;
  const strLit = /'([^'\\]|\\.)*'/g;
  const matches: { i: number; end: number; kind: 'kw' | 'str'; text: string }[] = [];
  let m: RegExpExecArray | null;
  const reKw = new RegExp(kw.source, kw.flags);
  while ((m = reKw.exec(data)) !== null) {
    matches.push({ i: m.index, end: m.index + m[0].length, kind: 'kw', text: m[0] });
  }
  while ((m = strLit.exec(data)) !== null) {
    matches.push({ i: m.index, end: m.index + m[0].length, kind: 'str', text: m[0] });
  }
  matches.sort((a, b) => a.i - b.i);
  let cursor = 0;
  for (const seg of matches) {
    if (seg.i < cursor) continue;
    if (seg.i > cursor) {
      parts.push(<span key={`t-${cursor}`}>{data.slice(cursor, seg.i)}</span>);
    }
    const color = seg.kind === 'kw' ? '#569cd6' : '#ce9178';
    parts.push(
      <span key={`s-${seg.i}`} style={{ color }}>
        {seg.text}
      </span>,
    );
    cursor = seg.end;
  }
  if (cursor < data.length) {
    parts.push(<span key={`e-${cursor}`}>{data.slice(cursor)}</span>);
  }
  return parts.length ? parts : data;
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100vw',
  height: '100vh',
  backgroundColor: 'rgba(0, 0, 0, 0.92)',
  zIndex: 9999,
  overflowY: 'auto',
  display: 'flex',
  alignItems: 'flex-start',
  justifyContent: 'center',
  paddingTop: '40px',
  paddingBottom: '40px',
  boxSizing: 'border-box',
};

const cardStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: '720px',
  backgroundColor: '#1a1f2e',
  borderRadius: '16px',
  padding: '32px',
  color: 'white',
  position: 'relative',
};

const AttackReplayVisualizer: React.FC<Props> = ({ challengeSlug, isSample, onClose }) => {
  const [steps, setSteps] = useState<Step[]>([]);
  const [currentStep, setCurrentStep] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opacity, setOpacity] = useState(1);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = isSample ? { sample: true } : {};
        const res = await api.get(`/api/challenges/replay/${encodeURIComponent(challengeSlug)}`, { params });
        if (!mounted) return;
        setSteps(res.data.steps || []);
        setCurrentStep(-1);
      } catch (e: any) {
        const d = e?.response?.data?.detail;
        setError(typeof d === 'string' ? d : e?.message || 'Failed to load replay');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [challengeSlug, isSample]);

  useEffect(() => {
    setOpacity(0);
    const t = setTimeout(() => setOpacity(1), 50);
    return () => clearTimeout(t);
  }, [currentStep]);

  useEffect(() => {
    if (!isPlaying) return;
    const total = steps.length;
    if (total === 0) return;
    const id = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= total - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1200);
    return () => clearInterval(id);
  }, [isPlaying, steps.length]);

  const totalSteps = steps.length;
  const step = currentStep >= 0 ? steps[currentStep] : null;

  const badgeForType = (t: string) => {
    const map: Record<string, { label: string; bg: string }> = {
      user_action: { label: 'User Action', bg: '#6b7280' },
      user_input: { label: 'Input', bg: '#2563eb' },
      http_request: { label: 'HTTP Request', bg: '#7c3aed' },
      server_processing: { label: 'Server', bg: '#d97706' },
      http_response: { label: 'Response', bg: '#16a34a' },
    };
    const b = map[t] || { label: t, bg: '#4b5563' };
    return (
      <span className="text-xs font-semibold px-2 py-1 rounded text-white" style={{ backgroundColor: b.bg }}>
        {b.label}
      </span>
    );
  };

  const renderDataBlock = () => {
    if (!step || step.data == null) return null;
    const d = step.data;
    let inner: React.ReactNode = d;
    if (step.type === 'http_request') {
      inner = renderHttpData(d);
    } else if (step.type === 'server_processing' && /SELECT|UPDATE|INSERT|DELETE/i.test(d)) {
      inner = renderSqlData(d);
    } else if (step.type === 'user_input') {
      inner = d;
    }
    return (
      <div
        className="mt-4 text-sm font-mono whitespace-pre-wrap"
        style={{
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          padding: 16,
          borderRadius: 8,
          borderLeft: step.type === 'user_input' ? '4px solid #ef4444' : undefined,
        }}
      >
        {inner}
      </div>
    );
  };

  const onPlayPause = () => {
    if (!isPlaying) {
      setCurrentStep((s) => (s < 0 ? 0 : s));
      setIsPlaying(true);
    } else {
      setIsPlaying(false);
    }
  };

  const onPrev = () => {
    setIsPlaying(false);
    setCurrentStep((s) => Math.max(0, s - 1));
  };

  const onNext = () => {
    setIsPlaying(false);
    setCurrentStep((s) => Math.min(totalSteps - 1, s + 1));
  };

  return createPortal(
    <div style={overlayStyle}>
      <div style={cardStyle}>
        <div className="flex items-center justify-between px-0 py-0 border-b border-gray-700 pb-3 mb-2 bg-transparent">
          <h2 className="text-lg font-bold">Attack Replay: {formatSlug(challengeSlug)}</h2>
          <button type="button" onClick={onClose} className="text-2xl leading-none px-2 hover:text-red-400" aria-label="Close">
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto w-full">
          {loading && <p className="text-center text-gray-400">Loading replay…</p>}
          {error && <p className="text-center text-red-400">{error}</p>}

          {!loading && !error && totalSteps > 0 && (
            <>
              <div className="flex flex-wrap gap-2 justify-center mb-2">
                {steps.map((_, i) => {
                  let cls = 'w-3 h-3 rounded-full border-2 border-gray-600 bg-transparent';
                  if (i < currentStep) cls = 'w-3 h-3 rounded-full bg-green-500 border-green-600';
                  else if (i === currentStep && currentStep >= 0)
                    cls =
                      'w-3 h-3 rounded-full bg-amber-500 border-amber-400 ring-2 ring-amber-400 ring-offset-2 ring-offset-gray-950 animate-pulse';
                  return <div key={i} className={cls} />;
                })}
              </div>
              <p className="text-center text-sm text-gray-400 mb-4">
                {currentStep < 0 ? 'Press Play to start' : `Step ${currentStep + 1} of ${totalSteps}`}
              </p>

              <div style={{ opacity }} className="transition-opacity duration-150">
                {currentStep < 0 && (
                  <div className="flex flex-col items-center justify-center py-16">
                    <p className="text-gray-400 mb-6">Press Play to begin the replay</p>
                    <button
                      type="button"
                      onClick={() => {
                        setCurrentStep(0);
                        setIsPlaying(true);
                      }}
                      className="px-6 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold"
                    >
                      ► Play
                    </button>
                  </div>
                )}

                {step && (
                  <div className="bg-gray-900/80 border border-gray-700 rounded-xl p-6 mb-6">
                    <div className="mb-3">{badgeForType(step.type)}</div>
                    <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                    <p className="text-gray-300">{step.description}</p>
                    {renderDataBlock()}
                  </div>
                )}
              </div>

              <div className="flex justify-center gap-3 pb-2">
                <button
                  type="button"
                  disabled={currentStep <= 0}
                  onClick={onPrev}
                  className="px-4 py-2 rounded bg-gray-700 disabled:opacity-40"
                >
                  ← Prev
                </button>
                <button type="button" onClick={onPlayPause} className="px-4 py-2 rounded bg-amber-600 hover:bg-amber-500">
                  {isPlaying ? '⏸ Pause' : '► Play'}
                </button>
                <button
                  type="button"
                  disabled={currentStep >= totalSteps - 1}
                  onClick={onNext}
                  className="px-4 py-2 rounded bg-gray-700 disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default AttackReplayVisualizer;
