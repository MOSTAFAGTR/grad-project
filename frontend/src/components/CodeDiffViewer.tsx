import React, { useState } from 'react';

type DiffLine = {
  type: 'added' | 'removed' | 'context';
  line_number_original: number | null;
  line_number_fixed: number | null;
  content: string;
  annotation: string | null;
};

interface CodeDiffViewerProps {
  diff: DiffLine[];
}

const tableCellBase: React.CSSProperties = {
  border: '1px solid #e5e7eb',
  verticalAlign: 'top',
  padding: '8px',
  fontFamily: 'monospace',
  fontSize: '13px',
  whiteSpace: 'pre-wrap',
  position: 'relative',
};

const lineNumberStyle: React.CSSProperties = {
  width: 48,
  minWidth: 48,
  color: '#6b7280',
  textAlign: 'right',
  paddingRight: 10,
  fontFamily: 'monospace',
  fontSize: '12px',
};

const annotationIconStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: 16,
  height: 16,
  borderRadius: '50%',
  border: '1px solid #9ca3af',
  color: '#374151',
  fontSize: 11,
  marginLeft: 8,
  cursor: 'pointer',
  backgroundColor: '#ffffff',
};

const tooltipStyle: React.CSSProperties = {
  position: 'absolute',
  top: 24,
  right: 8,
  zIndex: 50,
  maxWidth: 320,
  background: '#ffffff',
  border: '1px solid #e5e7eb',
  borderRadius: 8,
  padding: 12,
  fontSize: 13,
  color: '#111827',
  boxShadow: '0 8px 20px rgba(0,0,0,0.12)',
  fontFamily: 'sans-serif',
  whiteSpace: 'normal',
};

const CodeDiffViewer: React.FC<CodeDiffViewerProps> = ({ diff }) => {
  const [tooltipIndex, setTooltipIndex] = useState<number | null>(null);

  if (!diff || diff.length === 0) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontWeight: 700 }}>
        <span style={{ color: '#dc2626' }}>Vulnerable code</span>
        <span style={{ color: '#16a34a' }}>Fixed code</span>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed', background: '#ffffff', color: '#111827' }}>
        <tbody>
          {diff.map((line, idx) => {
            const leftBackground = line.type === 'removed' ? '#fee2e2' : 'transparent';
            const rightBackground = line.type === 'added' ? '#dcfce7' : 'transparent';
            return (
              <tr key={`${idx}-${line.type}`}>
                <td style={{ ...tableCellBase, ...lineNumberStyle, background: leftBackground }}>
                  {line.type !== 'added' ? line.line_number_original ?? '' : ''}
                </td>
                <td style={{ ...tableCellBase, background: leftBackground }}>
                  {line.type !== 'added' ? line.content : ''}
                  {line.type === 'removed' && line.annotation && (
                    <span
                      style={annotationIconStyle}
                      onMouseEnter={() => setTooltipIndex(idx)}
                      onMouseLeave={() => setTooltipIndex((current) => (current === idx ? null : current))}
                    >
                      ?
                    </span>
                  )}
                  {tooltipIndex === idx && line.type === 'removed' && line.annotation && <div style={tooltipStyle}>{line.annotation}</div>}
                </td>
                <td style={{ ...tableCellBase, ...lineNumberStyle, background: rightBackground }}>
                  {line.type !== 'removed' ? line.line_number_fixed ?? '' : ''}
                </td>
                <td style={{ ...tableCellBase, background: rightBackground }}>
                  {line.type !== 'removed' ? line.content : ''}
                  {line.type === 'added' && line.annotation && (
                    <span
                      style={annotationIconStyle}
                      onMouseEnter={() => setTooltipIndex(idx)}
                      onMouseLeave={() => setTooltipIndex((current) => (current === idx ? null : current))}
                    >
                      ?
                    </span>
                  )}
                  {tooltipIndex === idx && line.type === 'added' && line.annotation && <div style={tooltipStyle}>{line.annotation}</div>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default CodeDiffViewer;
