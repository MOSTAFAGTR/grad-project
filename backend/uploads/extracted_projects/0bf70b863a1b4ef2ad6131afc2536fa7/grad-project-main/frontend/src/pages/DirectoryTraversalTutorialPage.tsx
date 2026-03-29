import * as React from 'react';

const DirectoryTraversalTutorialPage: React.FC = () => {
  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Directory Traversal Tutorial</h1>
      <p className="text-gray-300">
        Directory traversal happens when untrusted file paths are concatenated directly. Attackers use payloads like
        <code className="mx-1">../../etc/passwd</code> to escape the intended folder. Fix by normalizing paths and ensuring the final path stays inside the allowed base directory.
      </p>
    </div>
  );
};

export default DirectoryTraversalTutorialPage;
