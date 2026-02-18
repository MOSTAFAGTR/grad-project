import type { FC } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FaCheckCircle } from 'react-icons/fa';

const typeConfig: Record<string, { title: string; subtitle: string; color: string }> = {
  'sql-injection': {
    title: 'Login successful',
    subtitle: 'The SQL injection attack was successful! You bypassed authentication.',
    color: 'cyan',
  },
  xss: {
    title: 'XSS attack successful',
    subtitle: 'The cross-site scripting payload was executed. The page reflected or stored your input.',
    color: 'pink',
  },
  csrf: {
    title: 'Transfer completed',
    subtitle: 'The CSRF attack was successful! The request was accepted without a valid token.',
    color: 'orange',
  },
  redirect: {
    title: 'Redirect successful',
    subtitle: 'The unvalidated redirect attack worked. The victim was sent to your chosen URL.',
    color: 'teal',
  },
  'command-injection': {
    title: 'Command executed',
    subtitle: 'The command injection was successful! Your payload ran on the server.',
    color: 'purple',
  },
};

const colorMap: Record<string, string> = {
  cyan: '#06b6d4',
  pink: '#d946ef',
  orange: '#fb923c',
  purple: '#8b5cf6',
  teal: '#14b8a6',
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