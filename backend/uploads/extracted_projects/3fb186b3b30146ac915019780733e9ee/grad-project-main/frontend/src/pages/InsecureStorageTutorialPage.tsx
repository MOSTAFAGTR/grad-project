import * as React from 'react';

const InsecureStorageTutorialPage: React.FC = () => {
  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Insecure Storage Tutorial</h1>
      <p className="text-gray-300">
        Storing passwords in plaintext makes any data leak immediately catastrophic. Attackers can dump storage and reuse credentials.
        The correct fix is one-way hashing before persistence and never exposing raw password values in debug or dump endpoints.
      </p>
    </div>
  );
};

export default InsecureStorageTutorialPage;
