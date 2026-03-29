import * as React from 'react';
import { Link } from 'react-router-dom';

const CommandInjectionTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">Command Injection Tutorial</h1>
      <p className="text-gray-400 mb-6">
        When user input is passed into shell commands (e.g. <code>ping</code>, <code>nslookup</code>) without validation,
        attackers can inject extra commands (e.g. <code>; id</code>, <code>| cat /etc/passwd</code>) and run arbitrary code.
      </p>
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 max-w-4xl mb-6">
        <h2 className="text-xl font-bold mb-2 text-purple-400">How to fix</h2>
        <ul className="list-disc list-inside text-gray-300 space-y-1">
          <li>Use an <strong>allowlist</strong> of allowed hosts; reject any other input with 400.</li>
          <li>Run the command with <code>subprocess.run([&quot;ping&quot;, &quot;-c&quot;, &quot;1&quot;, host], shell=False)</code> so the input is never interpreted by a shell.</li>
          <li>Never build a command string and pass it to <code>shell=True</code>.</li>
        </ul>
      </div>
      <div className="mt-8 flex gap-4">
        <Link to="/challenges/4/attack" className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded">
          Try the Attack
        </Link>
        <Link to="/challenges/4/fix" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
          Try the Fix
        </Link>
      </div>
    </div>
  );
};

export default CommandInjectionTutorialPage;
