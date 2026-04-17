import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

type ScanData = {
  projectId: string;
  project_id?: string;
  results?: any;
  overview?: any;
  summary?: any;
  findings?: any[];
  debug?: any;
} | null;

type ScanContextType = {
  scanData: ScanData;
  setScanData: (data: ScanData) => void;
  clearScanData: () => void;
};

const getUserScopedKey = () => {
  const userId = sessionStorage.getItem('user_id');
  return userId ? `scale.scanData.${userId}` : 'scale.scanData.guest';
};

const ScanContext = createContext<ScanContextType | undefined>(undefined);

export const ScanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [scanData, setScanDataState] = useState<ScanData>(() => {
    try {
      const raw = localStorage.getItem(getUserScopedKey());
      if (!raw) return null;
      const parsed = JSON.parse(raw) as ScanData | null;
      if (!parsed) return null;
      return {
        ...parsed,
        projectId: parsed.projectId || parsed.project_id || '',
      };
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const onUserChange = () => {
      try {
        const raw = localStorage.getItem(getUserScopedKey());
        if (!raw) {
          setScanDataState(null);
          return;
        }
        const parsed = JSON.parse(raw) as ScanData | null;
        if (!parsed) {
          setScanDataState(null);
          return;
        }
        setScanDataState({
          ...parsed,
          projectId: parsed.projectId || parsed.project_id || '',
        });
      } catch {
        setScanDataState(null);
      }
    };
    window.addEventListener('scale-user-changed', onUserChange);
    return () => window.removeEventListener('scale-user-changed', onUserChange);
  }, []);

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
      const key = getUserScopedKey();
      if (normalized) localStorage.setItem(key, JSON.stringify(normalized));
      else localStorage.removeItem(key);
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
