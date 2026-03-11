import React, { useState, ChangeEvent } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Scanner: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');
  const [projectId, setProjectId] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanResults, setScanResults] = useState<any>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
    setMessage('');
    setProjectId('');
    setScanResults(null);
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

      const response = await fetch(`${API_URL}/api/project/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await response.json();
      setProjectId(data.project_id || data.projectId || '');
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

      const response = await fetch(
        `${API_URL}/api/project/scan?project_id=${encodeURIComponent(projectId)}`,
        { method: 'POST' },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Scan failed');
      }
      const data = await response.json();
      setScanResults(data);
    } catch (err: any) {
      setMessage(err.message || 'Scan failed.');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-6">
      <div className="bg-gray-800/80 border border-gray-700 rounded-xl max-w-xl w-full p-8 shadow-2xl">
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

              <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-left border border-gray-700 rounded-lg overflow-hidden">
                  <thead className="bg-gray-800 text-gray-200">
                    <tr>
                      <th className="px-3 py-2 border-b border-gray-700">File</th>
                      <th className="px-3 py-2 border-b border-gray-700">Line</th>
                      <th className="px-3 py-2 border-b border-gray-700">Type</th>
                      <th className="px-3 py-2 border-b border-gray-700">Severity</th>
                      <th className="px-3 py-2 border-b border-gray-700">Fix</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(scanResults.findings || []).map((item: any, index: number) => {
                      const sev = (item.severity || '').toLowerCase();
                      const sevClass =
                        sev === 'high'
                          ? 'text-red-400'
                          : sev === 'medium'
                          ? 'text-yellow-300'
                          : sev === 'low'
                          ? 'text-green-400'
                          : 'text-gray-200';
                      return (
                        <tr key={index} className="odd:bg-gray-900 even:bg-gray-800">
                          <td className="px-3 py-2 border-b border-gray-800 font-mono text-xs">
                            {item.file}
                          </td>
                          <td className="px-3 py-2 border-b border-gray-800">
                            {item.line ?? '-'}
                          </td>
                          <td className="px-3 py-2 border-b border-gray-800">
                            {item.vulnerability_type || item.type}
                          </td>
                          <td className={`px-3 py-2 border-b border-gray-800 font-semibold ${sevClass}`}>
                            {item.severity || '-'}
                          </td>
                          <td className="px-3 py-2 border-b border-gray-800 text-xs text-gray-300">
                            {item.fix?.recommendation || '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Scanner;

