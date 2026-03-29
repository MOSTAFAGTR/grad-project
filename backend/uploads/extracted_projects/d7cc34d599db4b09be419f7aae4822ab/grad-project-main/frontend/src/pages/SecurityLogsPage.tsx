import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../lib/api';
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar } from 'recharts';

type SecurityLog = {
  id: number;
  user_id?: number | null;
  event_type: string;
  severity: string;
  payload?: string;
  endpoint?: string;
  ip_address?: string;
  geo_bucket?: string;
  session_id?: string;
  correlation_id?: string;
  context_type?: string;
  metadata?: Record<string, any>;
  created_at: string;
};

const severityClass = (sev: string) => {
  const s = (sev || '').toUpperCase();
  if (s === 'CRITICAL') return 'text-red-300 bg-red-900/50 border-red-700';
  if (s === 'HIGH') return 'text-orange-300 bg-orange-900/50 border-orange-700';
  if (s === 'MEDIUM') return 'text-yellow-200 bg-yellow-900/40 border-yellow-700';
  return 'text-blue-200 bg-blue-900/40 border-blue-700';
};

const SecurityLogsPage: React.FC = () => {
  const token = sessionStorage.getItem('token');
  const [severity, setSeverity] = useState('');
  const [eventType, setEventType] = useState('');
  const [contextType, setContextType] = useState('');
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<SecurityLog[]>([]);
  const [total, setTotal] = useState(0);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [stats, setStats] = useState<any>(null);

  const pageSize = 20;
  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total]);
  const sessionGroups = useMemo(() => {
    const map = new Map<string, number>();
    rows.forEach((r) => {
      const key = r.session_id || 'unknown';
      map.set(key, (map.get(key) || 0) + 1);
    });
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]).slice(0, 5);
  }, [rows]);

  const loadLogs = async () => {
    if (!token) return;
    const res = await axios.get(`${API_BASE_URL}/api/security/logs`, {
      headers: { Authorization: `Bearer ${token}` },
      params: {
        severity: severity || undefined,
        event_type: eventType || undefined,
        context_type: contextType || undefined,
        page,
        page_size: pageSize,
      },
    });
    setRows(res.data.items || []);
    setTotal(res.data.total || 0);
  };

  const loadStats = async () => {
    if (!token) return;
    const res = await axios.get(`${API_BASE_URL}/api/security/logs/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    setStats(res.data);
  };

  useEffect(() => {
    loadLogs().catch(() => {});
  }, [severity, eventType, contextType, page]);

  useEffect(() => {
    loadStats().catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-4">Security Monitoring</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <div className="bg-gray-800 border border-gray-700 rounded p-3">
          <p className="text-xs text-gray-400">Total events</p>
          <p className="text-2xl font-bold">{stats?.total_attacks ?? '-'}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded p-3">
          <p className="text-xs text-gray-400">Most common attack</p>
          <p className="text-xl font-semibold">{stats?.most_common_attack ?? '-'}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded p-3">
          <p className="text-xs text-gray-400">Top users</p>
          <p className="text-sm text-gray-200">
            {(stats?.top_users || []).map((u: any) => `#${u.user_id} (${u.count})`).join(' , ') || '-'}
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <div className="bg-gray-800 border border-gray-700 rounded p-3">
          <p className="text-xs text-gray-400">Unique attackers</p>
          <p className="text-2xl font-bold">{stats?.unique_attackers ?? '-'}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded p-3">
          <p className="text-xs text-gray-400">Challenge simulation events</p>
          <p className="text-2xl font-bold">{stats?.challenge_events ?? '-'}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded p-3">
          <p className="text-xs text-gray-400">Top frequency</p>
          <p className="text-xl font-semibold">{stats?.attack_frequency?.[0]?.event_type ?? '-'}</p>
        </div>
      </div>

      <div className="bg-gray-800 border border-gray-700 rounded p-3 mb-4 flex flex-wrap gap-2">
        <select
          value={severity}
          onChange={(e) => {
            setPage(1);
            setSeverity(e.target.value);
          }}
          className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm"
        >
          <option value="">All Severities</option>
          <option value="LOW">LOW</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HIGH">HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <input
          value={eventType}
          onChange={(e) => {
            setPage(1);
            setEventType(e.target.value);
          }}
          placeholder="Filter by event type"
          className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm"
        />
        <select
          value={contextType}
          onChange={(e) => {
            setPage(1);
            setContextType(e.target.value);
          }}
          className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm"
        >
          <option value="">All Contexts</option>
          <option value="real">real</option>
          <option value="challenge">challenge</option>
          <option value="system">system</option>
        </select>
      </div>

      <div className="bg-gray-800 border border-gray-700 rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-900">
            <tr>
              <th className="text-left px-3 py-2">Time</th>
              <th className="text-left px-3 py-2">Type</th>
              <th className="text-left px-3 py-2">Severity</th>
              <th className="text-left px-3 py-2">User</th>
              <th className="text-left px-3 py-2">Context</th>
              <th className="text-left px-3 py-2">Endpoint</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <React.Fragment key={r.id}>
                <tr
                  className="border-t border-gray-700 cursor-pointer hover:bg-gray-700/40"
                  onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                >
                  <td className="px-3 py-2">{new Date(r.created_at).toLocaleString()}</td>
                  <td className="px-3 py-2">{r.event_type}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-1 rounded border text-xs ${severityClass(r.severity)}`}>{r.severity}</span>
                  </td>
                  <td className="px-3 py-2">{r.user_id ?? '-'}</td>
                  <td className="px-3 py-2 text-xs">{r.context_type || '-'}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.endpoint || '-'}</td>
                </tr>
                {expanded === r.id && (
                  <tr className="border-t border-gray-700 bg-gray-900/70">
                    <td className="px-3 py-3 text-xs text-gray-200" colSpan={6}>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <p className="font-semibold text-gray-300 mb-1">Payload</p>
                          <pre className="bg-black/50 p-2 rounded whitespace-pre-wrap break-words">{r.payload || '-'}</pre>
                        </div>
                        <div>
                          <p className="font-semibold text-gray-300 mb-1">Metadata</p>
                          <pre className="bg-black/50 p-2 rounded whitespace-pre-wrap break-words">
                            {JSON.stringify(r.metadata || {}, null, 2)}
                          </pre>
                          <p className="mt-2 text-[11px] text-gray-400">
                            geo={r.geo_bucket || '-'} | session={r.session_id || '-'} | correlation={r.correlation_id || '-'}
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <button
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="px-3 py-1 rounded bg-gray-700 disabled:opacity-50"
        >
          Prev
        </button>
        <span className="text-sm text-gray-300">
          Page {page} / {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          className="px-3 py-1 rounded bg-gray-700 disabled:opacity-50"
        >
          Next
        </button>
      </div>

      <div className="mt-6 bg-gray-800 border border-gray-700 rounded p-4">
        <h2 className="text-lg font-bold mb-2">Timeline View</h2>
        <div className="h-48 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stats?.attack_trends || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="day" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-2 text-sm">
          {(stats?.timeline || []).slice(0, 12).map((t: any, idx: number) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="text-gray-500 text-xs">{new Date(t.created_at).toLocaleTimeString()}</span>
              <span className="text-cyan-300">User {t.user_id ?? '-'}</span>
              <span className="text-gray-400">→</span>
              <span>{t.event_type}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-6 bg-gray-800 border border-gray-700 rounded p-4">
        <h2 className="text-lg font-bold mb-2">Session Grouping (Current Page)</h2>
        <div className="space-y-2 text-sm">
          {sessionGroups.length === 0 && <p className="text-gray-400">No session data available.</p>}
          {sessionGroups.map(([sid, count]) => (
            <div key={sid} className="flex items-center justify-between bg-gray-900/50 border border-gray-700 rounded px-3 py-2">
              <span className="font-mono text-cyan-300 truncate">{sid}</span>
              <span className="text-gray-300">{count} events</span>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-6 bg-gray-800 border border-gray-700 rounded p-4">
        <h2 className="text-lg font-bold mb-2">Attack Heatmap (Hour)</h2>
        <div className="grid grid-cols-6 md:grid-cols-12 gap-1">
          {Array.from({ length: 24 }).map((_, h) => {
            const count = (stats?.timeline || []).filter((t: any) => new Date(t.created_at).getHours() === h).length;
            const shade = count > 8 ? 'bg-red-600' : count > 4 ? 'bg-orange-500' : count > 0 ? 'bg-yellow-500' : 'bg-gray-700';
            return (
              <div key={h} className={`${shade} rounded p-2 text-center text-[10px]`}>
                {h}:00 ({count})
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SecurityLogsPage;

