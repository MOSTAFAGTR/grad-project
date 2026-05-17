import * as React from 'react';
import ChallengeTutorialVideo from '../components/ChallengeTutorialVideo';

const XxeTutorialPage: React.FC = () => {
  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">XXE Tutorial</h1>
      <p className="text-gray-300 mb-6">
        XXE occurs when XML parsers allow external entities. Attackers can request local files like
        <code className="mx-1">/etc/passwd</code>. Fix by disabling DTD/external entities and rejecting suspicious XML declarations.
      </p>
      <ChallengeTutorialVideo challengeId={9} />
    </div>
  );
};

export default XxeTutorialPage;
