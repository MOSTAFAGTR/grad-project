import * as React from 'react';
import { Navigate, useParams } from 'react-router-dom';
import InsecureStorageAttackPage from './InsecureStorageAttackPage';
import InsecureStorageFixPage from './InsecureStorageFixPage';
import InsecureStorageTutorialPage from './InsecureStorageTutorialPage';

const InsecureStorageChallengePage: React.FC = () => {
  const { tab } = useParams<{ tab: string }>();

  if (tab === 'attack') return <InsecureStorageAttackPage />;
  if (tab === 'fix') return <InsecureStorageFixPage />;
  if (tab === 'tutorial') return <InsecureStorageTutorialPage />;

  return <Navigate to="/challenges/7/tutorial" replace />;
};

export default InsecureStorageChallengePage;

