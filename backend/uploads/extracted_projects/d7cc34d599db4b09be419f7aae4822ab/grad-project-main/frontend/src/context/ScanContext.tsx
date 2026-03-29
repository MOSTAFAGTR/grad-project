import React, { createContext, useContext, useMemo, useState } from 'react';

type ScanData = {
  projectId: string;
  project_id?: string;
  results: any;
  overview: any;
  summary: any;
  findings: any[];
  debug: any;
} | null;

type ScanContextType = {
  scanData: ScanData;
  setScanData: (data: ScanData) => void;
  clearScanData: () => void;
};

const STORAGE_KEY = 'scale.scanData';

const ScanContext = createContext<ScanContextType | undefined>(undefined);

export const ScanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [scanData, setScanDataState] = useState<ScanData>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as ScanData;
      return {
        ...parsed,
        projectId: parsed.projectId || parsed.project_id || '',
      };
    } catch {
      return null;
    }
  });

  const setScanData = (data: ScanData) => {
    const normalized = data
      ? {
          ...data,
          projectId: data.projectId || data.project_id || '',
          project_id: data.projectId || data.project_id || '',
        }
      : null;
    setScanDataState(normalized);
    try {
      if (normalized) localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore storage failures
    }
  };

  const clearScanData = () => setScanData(null);

  const value = useMemo(
    () => ({
      scanData,
      setScanData,
      clearScanData,
    }),
    [scanData],
  );

  return <ScanContext.Provider value={value}>{children}</ScanContext.Provider>;
};

export const useScanContext = () => {
  const ctx = useContext(ScanContext);
  if (!ctx) {
    throw new Error('useScanContext must be used inside ScanProvider');
  }
  return ctx;
};

