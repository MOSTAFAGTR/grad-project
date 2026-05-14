import * as React from 'react';
import { Navigate, useParams } from 'react-router-dom';
import XxeAttackPage from './XxeAttackPage';
import XxeFixPage from './XxeFixPage';
import XxeTutorialPage from './XxeTutorialPage';

const XxeChallengePage: React.FC = () => {
  const { tab } = useParams<{ tab: string }>();

  if (tab === 'attack') return <XxeAttackPage />;
  if (tab === 'fix') return <XxeFixPage />;
  if (tab === 'tutorial') return <XxeTutorialPage />;

  return <Navigate to="/challenges/9/tutorial" replace />;
};

export default XxeChallengePage;

