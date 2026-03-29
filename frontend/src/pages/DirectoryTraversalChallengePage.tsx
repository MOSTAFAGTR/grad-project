import * as React from 'react';
import { Navigate, useParams } from 'react-router-dom';
import DirectoryTraversalAttackPage from './DirectoryTraversalAttackPage';
import DirectoryTraversalFixPage from './DirectoryTraversalFixPage';
import DirectoryTraversalTutorialPage from './DirectoryTraversalTutorialPage';

const DirectoryTraversalChallengePage: React.FC = () => {
  const { tab } = useParams<{ tab: string }>();

  if (tab === 'attack') return <DirectoryTraversalAttackPage />;
  if (tab === 'fix') return <DirectoryTraversalFixPage />;
  if (tab === 'tutorial') return <DirectoryTraversalTutorialPage />;

  return <Navigate to="/challenges/8/tutorial" replace />;
};

export default DirectoryTraversalChallengePage;

