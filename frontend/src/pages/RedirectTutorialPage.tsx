import React from 'react';
import { Link } from 'react-router-dom';

const RedirectTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">Unvalidated Redirect Tutorial</h1>
      <p className="text-gray-400 mb-6">
        When an app redirects the user to a URL taken from the request (e.g. <code>?next=</code> or <code>?url=</code>) without checking it,
        attackers can send a link that looks trusted but sends the victim to a malicious site (phishing, malware).
      </p>
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 max-w-4xl mb-6">
        <h2 className="text-xl font-bold mb-2 text-teal-400">How to fix</h2>
        <ul className="list-disc list-inside text-gray-300 space-y-1">
          <li>Use an allowlist of allowed relative paths (e.g. <code>/dashboard</code>, <code>/profile</code>).</li>
          <li>Reject absolute URLs (<code>https://...</code>) and protocol-relative URLs (<code>//evil.com</code>).</li>
          <li>Return 400 or 403 for any disallowed target.</li>
        </ul>
      </div>
      <div className="mt-8 flex gap-4">
        <Link to="/challenges/10/attack" className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded">
          Try the Attack
        </Link>
        <Link to="/challenges/10/fix" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
          Try the Fix
        </Link>
      </div>
    </div>
  );
};

export default RedirectTutorialPage;
