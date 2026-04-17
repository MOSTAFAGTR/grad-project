import React, { useState, ChangeEvent, useEffect } from 'react';
import { api } from '../lib/api';
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
  fallback?: boolean;
  ai_available?: boolean;
  response?: string;
}

interface ProjectOverview {
  languages: string[];
  frameworks: string[];
  entry_points: string[];
  files_summary: Array<{ path: string; language: string; size: number }>;
  risk_indicators: string[];
  ai_summary?: string | null;
}

const SEVERITY_ORDER: Record<string, number> = {
  Critical: 0,
  High: 1,
  Medium: 2,
  Low: 3,
  Unknown: 4,
};

function DependenciesPanel({
  depData,
  depLoading,
  depError,
  depSeverityFilter,
  setDepSeverityFilter,
}: {
  depData: any;
  depLoading: boolean;
  depError: string;
  depSeverityFilter: string;
  setDepSeverityFilter: (v: string) => void;
}) {
  if (depLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-teal-500 border-t-transparent" />
      </div>
    );
  }
  if (depError) {
    return <div className="text-red-400 text-sm">{depError}</div>;
  }
  const vulns: any[] = depData?.dependency_vulns || [];
  const manifests: string[] = depData?.manifests_scanned || [];
  const totalV = depData?.total_dependency_vulns ?? 0;

  if (totalV === 0 && manifests.length === 0) {
    return (
      <p className="text-gray-400 text-sm">
        No dependency manifest files found in this project. Upload a project containing package.json or requirements.txt
        to enable dependency scanning.
      </p>
    );
  }

  const filtered =
    depSeverityFilter === 'all'
      ? vulns
      : vulns.filter((v) => (v.severity || '').toLowerCase() === depSeverityFilter.toLowerCase());
  const sorted = [...filtered].sort(
    (a, b) =>
      (SEVERITY_ORDER[a.severity as keyof typeof SEVERITY_ORDER] ?? 99) -
      (SEVERITY_ORDER[b.severity as keyof typeof SEVERITY_ORDER] ?? 99),
  );

  const hasCritHigh = vulns.some((v) => v.severity === 'Critical' || v.severity === 'High');
  const mediumOnly =
    vulns.length > 0 && vulns.every((v) => v.severity === 'Medium' || v.severity === 'Unknown' || v.severity === 'Low');

  if (manifests.length > 0 && totalV === 0) {
    return (
      <div className="space-y-4">
        <div className="p-3 rounded border border-green-700 bg-green-900/30 text-green-200 text-sm">
          No known vulnerabilities found across {manifests.length} manifest file{manifests.length === 1 ? '' : 's'}.
        </div>
        <table className="w-full text-xs border border-gray-700 rounded">
          <tbody>
            {manifests.map((m) => (
              <tr key={m} className="border-t border-gray-700">
                <td className="p-2 font-mono text-gray-300 break-all">{m}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div
        className={`p-3 rounded border text-sm ${
          hasCritHigh ? 'border-red-700 bg-red-900/30 text-red-100' : mediumOnly ? 'border-amber-600 bg-amber-900/30 text-amber-100' : 'border-gray-600 bg-gray-800/60 text-gray-200'
        }`}
      >
        {totalV} vulnerable dependenc{totalV === 1 ? 'y' : 'ies'} found across {manifests.length} manifest file
        {manifests.length === 1 ? '' : 's'}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="text-xs text-gray-400">Severity</label>
        <select
          className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm"
          value={depSeverityFilter}
          onChange={(e) => setDepSeverityFilter(e.target.value)}
        >
          <option value="all">All severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-xs text-left border border-gray-700 rounded">
          <thead className="bg-gray-800 text-gray-300">
            <tr>
              <th className="p-2">Package</th>
              <th className="p-2">Version</th>
              <th className="p-2">Ecosystem</th>
              <th className="p-2">CVE</th>
              <th className="p-2">Severity</th>
              <th className="p-2">Description</th>
              <th className="p-2">Fixed In</th>
              <th className="p-2">Advisory</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => {
              const eco = row.ecosystem || '';
              const ecoClass =
                eco === 'npm'
                  ? 'bg-blue-900/50 text-blue-200 border-blue-700'
                  : eco === 'PyPI'
                    ? 'bg-yellow-900/50 text-yellow-100 border-yellow-700'
                    : eco === 'Maven'
                      ? 'bg-orange-900/50 text-orange-100 border-orange-700'
                      : eco === 'Packagist'
                        ? 'bg-purple-900/50 text-purple-100 border-purple-700'
                        : 'bg-gray-800 text-gray-300 border-gray-600';
              const sev = row.severity || 'Unknown';
              const sevClass =
                sev === 'Critical'
                  ? 'bg-red-900/60 text-red-100'
                  : sev === 'High'
                    ? 'bg-orange-900/60 text-orange-100'
                    : sev === 'Medium'
                      ? 'bg-amber-900/60 text-amber-100'
                      : 'bg-gray-700 text-gray-200';
              const desc = String(row.description || '');
              const fix = row.fixed_in || '';
              return (
                <tr key={`${row.package}-${row.version}-${idx}`} className="border-t border-gray-700">
                  <td className="p-2 font-mono">{row.package}</td>
                  <td className="p-2 font-mono">{row.version}</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded border text-[10px] ${ecoClass}`}>{eco}</span>
                  </td>
                  <td className="p-2 font-mono text-[10px]">{row.cve_id || '—'}</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${sevClass}`}>{sev}</span>
                  </td>
                  <td className="p-2 max-w-xs text-gray-300" title={desc}>
                    {desc.length > 80 ? `${desc.slice(0, 80)}…` : desc}
                  </td>
                  <td className={`p-2 ${fix ? 'text-green-400' : 'text-red-400'}`}>{fix || 'No fix available'}</td>
                  <td className="p-2">
                    <a href={row.osv_url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">
                      View →
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <details className="group">
        <summary className="cursor-pointer text-sm text-gray-400 list-none [&::-webkit-details-marker]:hidden">
          Manifests scanned ({manifests.length} files)
        </summary>
        <ul className="mt-2 text-xs font-mono text-gray-500 list-disc pl-5 space-y-1">
          {manifests.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      </details>
    </div>
  );
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
  const [resultTab, setResultTab] = useState<'findings' | 'dependencies'>('findings');
  const [depData, setDepData] = useState<any>(null);
  const [depLoading, setDepLoading] = useState(false);
  const [depError, setDepError] = useState('');
  const [depSeverityFilter, setDepSeverityFilter] = useState<string>('all');
  const [depRefreshTick, setDepRefreshTick] = useState(0);
  const [mentorNoAiNote, setMentorNoAiNote] = useState('');

  useEffect(() => {
    if (!scanData) return;
    setScanResults(scanData.results || null);
    setProjectOverview(scanData.overview || null);
    setProjectId(scanData.projectId || '');
    setSelectedFinding((scanData.results?.findings || [])[0] || null);
  }, [scanData]);

  useEffect(() => {
    if (!projectId || scanResults) return;
    const controller = new AbortController();
    api
      .get(`/api/project/${encodeURIComponent(projectId)}`, { signal: controller.signal })
      .then(() => {
        setMessage('Restored project context. Click "Scan Project" to fetch latest findings.');
      })
      .catch((err: any) => {
        if (err?.name === 'AbortError') return;
        setMessage(err?.response?.data?.detail || err.message || 'Unable to restore project context.');
      });
    return () => controller.abort();
  }, [projectId, scanResults]);

  useEffect(() => {
    if (resultTab !== 'dependencies' || !projectId) return;
    let cancelled = false;
    setDepLoading(true);
    setDepError('');
    api
      .get(`/api/project/${encodeURIComponent(projectId)}/dependencies`)
      .then((res) => {
        if (!cancelled) setDepData(res.data || {});
      })
      .catch((err: any) => {
        if (!cancelled) setDepError(err?.response?.data?.detail || err.message || 'Failed to load');
      })
      .finally(() => {
        if (!cancelled) setDepLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [resultTab, projectId, depRefreshTick]);

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

      // Use shared api instance so Authorization is attached consistently.
      // Do not set multipart Content-Type manually; axios injects boundary automatically.
      const response = await api.post('/api/project/upload', formData);
      const data = response.data;
      const resolvedProjectId =
        data.project_id ||
        data.projectId ||
        (typeof data.project_folder === 'string'
          ? data.project_folder.split('/').filter(Boolean).pop()
          : '');
      setProjectId(resolvedProjectId || '');
      setProjectOverview(null);

      if (resolvedProjectId) {
        const analysisResponse = await api.post(
          `/api/project/analyze-structure?project_id=${encodeURIComponent(resolvedProjectId)}`,
        );
        const analysisData: ProjectOverview = analysisResponse.data;
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

      const response = await api.post(`/api/project/scan?project_id=${encodeURIComponent(projectId)}`);
      const data = response.data;
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
    setMentorNoAiNote('');

    if (mentorCache[key]) {
      setMentorData(mentorCache[key]);
      return;
    }

    setMentorLoading(true);
    try {
      const response = await api.post('/api/ai/analyze-code', {
          code,
          language: finding.language || 'unknown',
          vulnerability_type: getFindingType(finding),
          severity: finding.severity || 'Medium',
          file: finding.file,
          line: finding.line || 0,
      });
      const data = response.data as MentorResponse;
      if (data.fallback) {
        setMentorData(null);
        setMentorNoAiNote(data.response || 'AI mentor is not configured.');
      } else {
        setMentorData(data);
        setMentorCache((prev) => ({ ...prev, [key]: data }));
      }
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
              <div className="flex gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => setResultTab('findings')}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold ${
                    resultTab === 'findings' ? 'bg-teal-600 text-white' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Findings
                </button>
                <button
                  type="button"
                  onClick={() => setResultTab('dependencies')}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold ${
                    resultTab === 'dependencies' ? 'bg-teal-600 text-white' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Dependencies
                </button>
              </div>

              {resultTab === 'dependencies' && (
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <p className="text-sm text-gray-400">
                    Dependency scan runs in background. Results may take up to 30 seconds after the main scan completes.
                  </p>
                  <button
                    type="button"
                    onClick={() => setDepRefreshTick((t) => t + 1)}
                    className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-gray-700 hover:bg-gray-600 text-white shrink-0"
                  >
                    Refresh
                  </button>
                </div>
              )}

              {resultTab === 'findings' && (
                <>
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
                </>
              )}

              {resultTab === 'dependencies' && (
                <DependenciesPanel
                  depData={depData}
                  depLoading={depLoading}
                  depError={depError}
                  depSeverityFilter={depSeverityFilter}
                  setDepSeverityFilter={setDepSeverityFilter}
                />
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

            {mentorNoAiNote && (
              <div className="mb-4 p-3 rounded border border-amber-700 bg-amber-900/30 text-amber-100 text-sm">
                {mentorNoAiNote}
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

