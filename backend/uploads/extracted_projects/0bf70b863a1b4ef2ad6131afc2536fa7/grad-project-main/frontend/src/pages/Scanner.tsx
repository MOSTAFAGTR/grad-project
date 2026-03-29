import React, { useState, ChangeEvent, useEffect } from 'react';
import { API_BASE_URL } from '../lib/api';
import { useNavigate } from 'react-router-dom';
import { useScanContext } from '../context/ScanContext';
import { DEFAULT_PAYLOADS, getDefaultPayload } from '../utils/payloads';

interface Finding {
  file: string;
  line?: number;
  vulnerability_type?: string;
  type?: string;
  severity?: 'Low' | 'Medium' | 'High' | string;
  code_snippet?: string;
  code?: string;
  language?: string;
  fix?: { recommendation?: string };
}

interface MentorResponse {
  explanation: string;
  attack_scenario: string;
  payload_example: string;
  technical_breakdown: string;
  fix_recommendation: string;
  secure_code_example: string;
  critique: string;
  confidence: 'Low' | 'Medium' | 'High';
}

interface ProjectOverview {
  languages: string[];
  frameworks: string[];
  entry_points: string[];
  files_summary: Array<{ path: string; language: string; size: number }>;
  risk_indicators: string[];
  ai_summary?: string | null;
}

const Scanner: React.FC = () => {
  const navigate = useNavigate();
  const { scanData, setScanData, clearScanData } = useScanContext();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');
  const [projectId, setProjectId] = useState<string>(scanData?.projectId || '');
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanResults, setScanResults] = useState<any>(scanData?.results || null);
  const [projectOverview, setProjectOverview] = useState<ProjectOverview | null>(scanData?.overview || null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [mentorOpen, setMentorOpen] = useState(false);
  const [mentorLoading, setMentorLoading] = useState(false);
  const [mentorError, setMentorError] = useState('');
  const [mentorData, setMentorData] = useState<MentorResponse | null>(null);
  const [mentorEditedCode, setMentorEditedCode] = useState('');
  const [mentorCache, setMentorCache] = useState<Record<string, MentorResponse>>({});
  const [mentorTarget, setMentorTarget] = useState<Finding | null>(null);

  useEffect(() => {
    if (!scanData) return;
    setScanResults(scanData.results || null);
    setProjectOverview(scanData.overview || null);
    setProjectId(scanData.projectId || '');
    setSelectedFinding((scanData.results?.findings || [])[0] || null);
  }, [scanData]);

  useEffect(() => {
    const token = sessionStorage.getItem('token') || '';
    if (!projectId || scanResults || !token) return;
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/api/project/${encodeURIComponent(projectId)}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Project no longer exists');
        }
        return res.json();
      })
      .then(() => {
        setMessage('Restored project context. Click "Scan Project" to fetch latest findings.');
      })
      .catch((err: any) => {
        if (err?.name === 'AbortError') return;
        setMessage(err.message || 'Unable to restore project context.');
      });
    return () => controller.abort();
  }, [projectId, scanResults]);

  const findings = scanResults?.findings || [];
  const severitySummary = findings.reduce(
    (acc: { High: number; Medium: number; Low: number }, item: any) => {
      const sev = String(item.severity || '').toLowerCase();
      if (sev === 'high') acc.High += 1;
      else if (sev === 'medium') acc.Medium += 1;
      else if (sev === 'low') acc.Low += 1;
      return acc;
    },
    { High: 0, Medium: 0, Low: 0 },
  );

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
    setMessage('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Please select a ZIP file first.');
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
      setMessage('Only .zip files are allowed.');
      return;
    }

    try {
      setUploading(true);
      setMessage('');

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_BASE_URL}/api/project/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem('token') || ''}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await response.json();
      const resolvedProjectId =
        data.project_id ||
        data.projectId ||
        (typeof data.project_folder === 'string'
          ? data.project_folder.split('/').filter(Boolean).pop()
          : '');
      setProjectId(resolvedProjectId || '');
      setProjectOverview(null);

      if (resolvedProjectId) {
        const analysisResponse = await fetch(
          `${API_BASE_URL}/api/project/analyze-structure?project_id=${encodeURIComponent(resolvedProjectId)}`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${sessionStorage.getItem('token') || ''}`,
            },
          },
        );
        if (analysisResponse.ok) {
          const analysisData: ProjectOverview = await analysisResponse.json();
          setProjectOverview(analysisData);
          setScanData({
            projectId: resolvedProjectId,
            results: null,
            overview: analysisData,
            summary: null,
            findings: [],
            debug: null,
          });
        }
      }

      setMessage('Upload successful!');
    } catch (err: any) {
      setMessage(err.message || 'Upload failed.');
      setProjectId('');
    } finally {
      setUploading(false);
    }
  };

  const handleScan = async () => {
    if (!projectId) return;
    try {
      setScanning(true);
      setMessage('');
      setScanResults(null);
      setSelectedFinding(null);

      const response = await fetch(
        `${API_BASE_URL}/api/project/scan?project_id=${encodeURIComponent(projectId)}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem('token') || ''}`,
          },
        },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Scan failed');
      }
      const data = await response.json();
      setScanResults(data);
      setScanData({
        projectId,
        results: data,
        overview: projectOverview,
        summary: data.summary || null,
        findings: data.findings || [],
        debug: data.debug || null,
      });
      if (data.message) setMessage(data.message);
      setSelectedFinding((data.findings || [])[0] || null);
    } catch (err: any) {
      setMessage(err.message || 'Scan failed.');
    } finally {
      setScanning(false);
    }
  };

  const exportResultsAsJson = () => {
    if (!scanResults) return;
    const blob = new Blob([JSON.stringify(scanResults, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scan-results-${projectId || 'project'}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const getFindingType = (finding: Finding) =>
    finding.vulnerability_type || finding.type || 'Unknown';

  const getFindingCode = (finding: Finding) =>
    finding.code_snippet || finding.code || '';

  const severityBadgeClass = (severity: string) => {
    const sev = (severity || '').toLowerCase();
    if (sev === 'high') return 'bg-red-900/40 text-red-300 border-red-700';
    if (sev === 'medium') return 'bg-orange-900/40 text-orange-300 border-orange-700';
    if (sev === 'low') return 'bg-blue-900/40 text-blue-300 border-blue-700';
    return 'bg-gray-800 text-gray-300 border-gray-700';
  };

  const cacheKeyFor = (finding: Finding, code: string) =>
    `${finding.file}:${finding.line || 0}:${getFindingType(finding)}:${code}`;

  const requestMentorAnalysis = async (finding: Finding, codeOverride?: string) => {
    const code = codeOverride ?? getFindingCode(finding);
    const key = cacheKeyFor(finding, code);

    setMentorOpen(true);
    setMentorTarget(finding);
    setMentorEditedCode(code);
    setMentorError('');

    if (mentorCache[key]) {
      setMentorData(mentorCache[key]);
      return;
    }

    setMentorLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/analyze-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${sessionStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify({
          code,
          language: finding.language || 'unknown',
          vulnerability_type: getFindingType(finding),
          severity: finding.severity || 'Medium',
          file: finding.file,
          line: finding.line || 0,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'AI mentor request failed');
      }
      const data: MentorResponse = await response.json();
      setMentorData(data);
      setMentorCache((prev) => ({ ...prev, [key]: data }));
    } catch (err: any) {
      setMentorError(err.message || 'AI mentor request failed');
      setMentorData(null);
    } finally {
      setMentorLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-start justify-center p-6 overflow-x-hidden max-w-full">
      <div className="bg-gray-800/80 border border-gray-700 rounded-xl max-w-5xl w-full p-8 shadow-2xl overflow-x-hidden">
        <h1 className="text-2xl font-bold mb-4">Security Scanner</h1>
        <p className="text-sm text-gray-400 mb-6">
          Upload a compressed project (.zip) to run it through the security training scanner.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Project ZIP file</label>
            <input
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              className="w-full text-sm text-gray-200 bg-gray-900 border border-gray-700 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading || !selectedFile}
            className={`w-full py-2 rounded-lg font-semibold transition ${
              uploading || !selectedFile
                ? 'bg-blue-900 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {uploading ? 'Uploading...' : 'Upload Project'}
          </button>

          {message && (
            <div className="mt-2 text-sm">
              <span className={projectId ? 'text-green-400' : 'text-red-400'}>{message}</span>
            </div>
          )}

          {projectId && (
            <div className="mt-4 space-y-2">
              <p className="text-sm text-gray-300">
                <span className="font-semibold">Project ID:</span> <span className="font-mono">{projectId}</span>
              </p>
              <button
                onClick={handleScan}
                disabled={scanning}
                className={`w-full py-2 rounded-lg font-semibold transition ${
                  scanning ? 'bg-teal-900 text-gray-400 cursor-not-allowed' : 'bg-teal-600 hover:bg-teal-700'
                }`}
              >
                {scanning ? 'Scanning project...' : 'Scan Project'}
              </button>
              <button
                onClick={() => {
                  setProjectId('');
                  setScanResults(null);
                  setProjectOverview(null);
                  setSelectedFinding(null);
                  setMentorOpen(false);
                  setMentorData(null);
                  setMentorError('');
                  clearScanData();
                  setMessage('Project state cleared.');
                }}
                className="w-full py-2 rounded-lg font-semibold bg-gray-700 hover:bg-gray-600 transition"
              >
                Clear Project
              </button>
            </div>
          )}

          {scanResults && (
            <div className="mt-8">
              <h2 className="text-xl font-bold mb-2">Scan Results</h2>
              <p className="text-sm text-gray-300">
                Total Vulnerabilities:{' '}
                <span className="font-semibold">
                  {scanResults.total_vulnerabilities ?? scanResults.total ?? 0}
                </span>
              </p>
              <p className="text-sm text-gray-300 mb-4">
                Risk Score:{' '}
                <span className="font-semibold">
                  {scanResults.risk?.total_score ?? 'N/A'} ({scanResults.risk?.risk_level ?? 'Unknown'})
                </span>
              </p>
              <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
                <div className="bg-red-900/40 border border-red-700 rounded p-2">
                  <span className="text-red-300 font-bold">High:</span> {severitySummary.High}
                </div>
                <div className="bg-yellow-900/40 border border-yellow-700 rounded p-2">
                  <span className="text-yellow-300 font-bold">Medium:</span> {severitySummary.Medium}
                </div>
                <div className="bg-green-900/40 border border-green-700 rounded p-2">
                  <span className="text-green-300 font-bold">Low:</span> {severitySummary.Low}
                </div>
              </div>
              <div className="mb-4 flex flex-wrap gap-2">
                <button
                  onClick={exportResultsAsJson}
                  className="px-3 py-2 text-xs rounded bg-indigo-600 hover:bg-indigo-700 font-semibold"
                >
                  Export Results (JSON)
                </button>
              </div>

              {findings.length === 0 && (
                <div className="mb-4 bg-amber-900/40 border border-amber-600 rounded p-3 text-sm text-amber-200">
                  {scanResults.message || 'No vulnerabilities detected OR not supported by current scanner depth'}
                </div>
              )}

              <div className="space-y-3 max-w-full overflow-x-hidden">
                {findings.map((item: any, index: number) => {
                  const vType = getFindingType(item);
                  const codeSnippet = getFindingCode(item) || '// No code snippet';
                  return (
                    <div
                      key={index}
                      className={`bg-gray-900 border rounded-xl p-4 cursor-pointer transition ${
                        selectedFinding === item ? 'border-blue-500' : 'border-gray-700 hover:border-gray-600'
                      }`}
                      onClick={() => setSelectedFinding(item)}
                    >
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <span className="text-xs font-mono text-gray-300 break-words [overflow-wrap:anywhere]">
                          {item.file} : {item.line ?? '-'}
                        </span>
                        <span className="text-xs px-2 py-1 rounded-full border bg-gray-800 text-cyan-300 border-cyan-700">
                          {vType}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full border ${severityBadgeClass(item.severity || '')}`}>
                          {item.severity || '-'}
                        </span>
                      </div>

                      <pre className="max-h-[200px] overflow-y-auto bg-slate-900 p-3 rounded-xl text-xs text-green-300 font-mono whitespace-pre-wrap break-words [overflow-wrap:anywhere] mb-3">
{codeSnippet}
                      </pre>

                      <div className="text-xs text-gray-300 mb-3 whitespace-pre-wrap break-words [overflow-wrap:anywhere]">
                        <span className="font-semibold text-gray-200">Fix:</span> {item.fix?.recommendation || '—'}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            requestMentorAnalysis(item);
                          }}
                          className="text-xs px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-700 font-semibold"
                        >
                          Explain Attack
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate('/attack-lab', {
                              state: {
                                vulnerability_type: vType,
                                code: codeSnippet,
                                payload: DEFAULT_PAYLOADS[item.type || ''] || getDefaultPayload(vType) || '',
                              },
                            });
                          }}
                          className="text-xs px-3 py-2 rounded bg-red-700 hover:bg-red-600 font-semibold"
                        >
                          Simulate Attack
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {selectedFinding && (
                <div className="mt-4 bg-gray-900 border border-gray-700 rounded-lg p-4">
                  <h3 className="text-sm font-bold text-blue-300 mb-2">Selected Vulnerability Details</h3>
                  <div className="text-xs text-gray-300 space-y-1 mb-3">
                    <p><span className="font-semibold">Type:</span> {selectedFinding.vulnerability_type || selectedFinding.type}</p>
                    <p><span className="font-semibold">File:</span> <span className="font-mono">{selectedFinding.file}</span></p>
                    <p><span className="font-semibold">Line:</span> {selectedFinding.line ?? '-'}</p>
                    <p><span className="font-semibold">Severity:</span> {selectedFinding.severity ?? '-'}</p>
                  </div>
                  <pre className="bg-slate-900 border border-gray-800 rounded-xl p-3 text-xs text-green-300 max-h-[200px] overflow-y-auto whitespace-pre-wrap break-words [overflow-wrap:anywhere]">
{selectedFinding.code_snippet || selectedFinding.code || '// No code snippet'}
                  </pre>
                </div>
              )}
              {scanResults.debug && (
                <div className="mt-4 bg-gray-900 border border-gray-700 rounded-lg p-4">
                  <h3 className="text-sm font-bold text-purple-300 mb-2">Scanner Debug</h3>
                  <p className="text-xs text-gray-300">
                    Files scanned: {scanResults.debug.files_scanned ?? 0} | Files with matches:{' '}
                    {scanResults.debug.files_with_matches ?? 0}
                  </p>
                </div>
              )}
            </div>
          )}

          {projectOverview && (
            <div className="mt-8 bg-gray-900 border border-gray-700 rounded-lg p-4">
              <h2 className="text-xl font-bold mb-3">Project Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-cyan-300 font-semibold mb-1">Languages</p>
                  <p className="text-gray-300">{projectOverview.languages.join(', ') || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-cyan-300 font-semibold mb-1">Frameworks</p>
                  <p className="text-gray-300">{projectOverview.frameworks.join(', ') || 'Not detected'}</p>
                </div>
                <div>
                  <p className="text-cyan-300 font-semibold mb-1">Entry points</p>
                  <p className="text-gray-300">{projectOverview.entry_points.join(', ') || 'Not detected'}</p>
                </div>
                <div>
                  <p className="text-cyan-300 font-semibold mb-1">Risk indicators</p>
                  <p className="text-gray-300">{projectOverview.risk_indicators.join(' | ') || 'No obvious indicators'}</p>
                </div>
              </div>
              {projectOverview.ai_summary && (
                <div className="mt-3 p-3 rounded bg-indigo-900/30 border border-indigo-700 text-sm text-indigo-100 whitespace-pre-wrap">
                  {projectOverview.ai_summary}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {mentorOpen && (
        <div className="fixed inset-0 bg-black/70 z-50 flex justify-end">
          <div className="w-full max-w-2xl h-full bg-gray-900 border-l border-gray-700 p-5 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-indigo-300">Adaptive AI Security Mentor</h2>
              <button
                onClick={() => setMentorOpen(false)}
                className="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 text-sm"
              >
                Close
              </button>
            </div>

            {mentorTarget && (
              <div className="mb-4 text-xs text-gray-300">
                <p><span className="font-semibold">Target:</span> {mentorTarget.file}:{mentorTarget.line || 0}</p>
                <p><span className="font-semibold">Type:</span> {getFindingType(mentorTarget)}</p>
                <p><span className="font-semibold">Severity:</span> {mentorTarget.severity || 'Medium'}</p>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-200 mb-2">Editable Code Snippet</label>
              <textarea
                className="w-full h-36 bg-black border border-gray-700 rounded p-3 text-xs font-mono text-green-300"
                value={mentorEditedCode}
                onChange={(e) => setMentorEditedCode(e.target.value)}
              />
              <button
                onClick={() => mentorTarget && requestMentorAnalysis(mentorTarget, mentorEditedCode)}
                disabled={mentorLoading || !mentorTarget}
                className="mt-2 text-xs px-3 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 font-semibold"
              >
                {mentorLoading ? 'Analyzing...' : 'Re-analyze'}
              </button>
            </div>

            {mentorLoading && (
              <div className="mb-4 p-3 rounded border border-indigo-700 bg-indigo-900/30 text-indigo-200 text-sm">
                AI mentor is analyzing this vulnerability...
              </div>
            )}

            {mentorError && (
              <div className="mb-4 p-3 rounded border border-red-700 bg-red-900/30 text-red-200 text-sm">
                {mentorError}
              </div>
            )}

            {mentorData && (
              <div className="space-y-3">
                <div className="p-3 rounded border border-gray-700 bg-gray-800">
                  <h3 className="font-bold text-gray-100 mb-1">Vulnerability Explanation</h3>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap">{mentorData.explanation}</p>
                </div>

                <div className="p-3 rounded border border-red-700 bg-red-900/20">
                  <h3 className="font-bold text-red-300 mb-1">Attack Scenario</h3>
                  <p className="text-sm text-red-100 whitespace-pre-wrap">{mentorData.attack_scenario}</p>
                </div>

                <div className="p-3 rounded border border-red-700 bg-red-900/20">
                  <h3 className="font-bold text-red-300 mb-1">Payload Example</h3>
                  <pre className="text-xs text-red-100 whitespace-pre-wrap font-mono">{mentorData.payload_example}</pre>
                </div>

                <div className="p-3 rounded border border-gray-700 bg-gray-800">
                  <h3 className="font-bold text-gray-100 mb-1">Technical Breakdown</h3>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap">{mentorData.technical_breakdown}</p>
                </div>

                <div className="p-3 rounded border border-green-700 bg-green-900/20">
                  <h3 className="font-bold text-green-300 mb-1">Fix Recommendation</h3>
                  <p className="text-sm text-green-100 whitespace-pre-wrap">{mentorData.fix_recommendation}</p>
                </div>

                <div className="p-3 rounded border border-green-700 bg-green-900/20">
                  <h3 className="font-bold text-green-300 mb-1">Secure Code Example</h3>
                  <pre className="text-xs text-green-100 whitespace-pre-wrap font-mono">{mentorData.secure_code_example}</pre>
                </div>

                <div className="p-3 rounded border border-gray-700 bg-gray-800">
                  <h3 className="font-bold text-gray-100 mb-1">Critique</h3>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap">{mentorData.critique}</p>
                </div>

                <div className="text-xs text-indigo-200 font-semibold">
                  Confidence: {mentorData.confidence}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Scanner;

