import type { FC } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FaCheckCircle } from 'react-icons/fa';

const typeConfig: Record<
  string,
  { title: string; subtitle: string; color: string; xp: number; explanation: string }
> = {
  'sql-injection': {
    title: 'Login successful',
    subtitle: 'The SQL injection attack was successful! You bypassed authentication.',
    color: 'cyan',
    xp: 150,
    explanation:
      'The application built SQL queries by concatenating user input directly, allowing your payload to change the WHERE clause and bypass authentication. Use parameterized queries and avoid string concatenation to fix this.',
  },
  xss: {
    title: 'XSS attack successful',
    subtitle: 'The cross-site scripting payload was executed. The page reflected or stored your input.',
    color: 'pink',
    xp: 120,
    explanation:
      'The page rendered untrusted input without proper output encoding, allowing your script to run in the victim’s browser. To fix this, perform context-aware output encoding and avoid using dangerous sinks like innerHTML.',
  },
  csrf: {
    title: 'Transfer completed',
    subtitle: 'The CSRF attack was successful! The request was accepted without a valid token.',
    color: 'orange',
    xp: 130,
    explanation:
      'The bank endpoint changed state (money transfer) solely based on cookies, without requiring any CSRF token or same-site cookie protection. Always use anti-CSRF tokens and SameSite cookies for state-changing endpoints.',
  },
  redirect: {
    title: 'Redirect successful',
    subtitle: 'The unvalidated redirect attack worked. The victim was sent to your chosen URL.',
    color: 'teal',
    xp: 110,
    explanation:
      'The application redirected to a URL taken directly from user input without validation, enabling open redirects. Restrict redirects to an allowlist of relative paths and reject external URLs.',
  },
  'command-injection': {
    title: 'Command executed',
    subtitle: 'The command injection was successful! Your payload ran on the server.',
    color: 'purple',
    xp: 160,
    explanation:
      'The server passed your input directly to a shell command, letting you inject extra commands. Use high-level APIs (no shell), avoid shell=True, and validate or whitelist input.',
  },
  'broken-auth': {
    title: 'Admin access obtained',
    subtitle: 'You bypassed the login controls and gained an administrator session.',
    color: 'red',
    xp: 140,
    explanation:
      'The login logic trusted crafted input to short-circuit authentication and grant admin access. Authentication must never rely on user-controlled SQL fragments or shortcut conditions; always validate credentials strictly.',
  },
  'security-misc': {
    title: 'Configuration exposed',
    subtitle: 'You discovered an exposed admin/config endpoint leaking sensitive settings.',
    color: 'yellow',
    xp: 140,
    explanation:
      'The service was deployed with sensitive admin/debug endpoints exposed in production, leaking secrets and internal configuration. Disable debug mode, protect admin interfaces, and never expose configuration or environment data.',
  },
  'directory-traversal': {
    title: 'Traversal successful',
    subtitle: 'You accessed a restricted file using path traversal.',
    color: 'orange',
    xp: 130,
    explanation:
      "The endpoint joined user input directly to a file path, so '../' escaped the intended directory. Fix by normalizing and validating final paths stay inside the allowed base folder.",
  },
  xxe: {
    title: 'XXE successful',
    subtitle: 'The XML payload extracted sensitive system data.',
    color: 'purple',
    xp: 140,
    explanation:
      'The parser accepted external entities, allowing attacker-controlled XML to read local files. Disable DTD/external entities and reject suspicious XML declarations.',
  },
  'insecure-storage': {
    title: 'Storage exposure successful',
    subtitle: 'You exposed plaintext credentials from storage.',
    color: 'red',
    xp: 130,
    explanation:
      'Passwords were stored in plaintext and leaked through dump/debug output. Use one-way hashing for credentials and avoid exposing raw secrets.',
  },
};

const colorMap: Record<string, string> = {
  cyan: '#06b6d4',
  pink: '#d946ef',
  orange: '#fb923c',
  purple: '#8b5cf6',
  teal: '#14b8a6',
  red: '#f97373',
  yellow: '#facc15',
};

const AttackSuccessPage: FC = () => {
  const [searchParams] = useSearchParams();
  const type = searchParams.get('type') ?? 'xss';
  const config = typeConfig[type] ?? typeConfig.xss;
  const accent = colorMap[config.color] ?? colorMap.cyan;

  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-6">
      <div
        className="w-24 h-24 rounded-full flex items-center justify-center mb-6 animate-pulse"
        style={{ backgroundColor: `${accent}20`, border: `3px solid ${accent}` }}
      >
        <FaCheckCircle className="text-5xl" style={{ color: accent }} />
      </div>
      <h1 className="text-4xl font-bold mb-3" style={{ color: accent }}>
        {config.title}
      </h1>
      <p className="text-gray-400 max-w-lg mb-8">
        {config.subtitle}
      </p>
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 max-w-2xl text-left mb-6">
        <h2 className="text-lg font-semibold mb-2" style={{ color: accent }}>
          Challenge Summary
        </h2>
        <p className="text-sm text-gray-300 mb-2">
          <span className="font-semibold">XP gained:</span> <span style={{ color: accent }}>{config.xp}</span>
        </p>
        <p className="text-sm text-gray-300">
          {config.explanation}
        </p>
      </div>
      <div className="flex gap-4">
        <Link
          to="/challenges"
          className="px-8 py-3 font-bold rounded-lg transition-colors"
          style={{
            backgroundColor: accent,
            color: '#fff',
          }}
        >
          Return to Challenges
        </Link>
        <Link
          to="/home"
          className="px-8 py-3 font-bold rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
        >
          Dashboard
        </Link>
      </div>
    </div>
  );
};

export default AttackSuccessPage;