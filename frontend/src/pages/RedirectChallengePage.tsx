import * as React from 'react';
import { useParams, Navigate } from 'react-router-dom';
import RedirectAttackPage from './RedirectAttackPage';
import RedirectFixPage from './RedirectFixPage';
import RedirectTutorialPage from './RedirectTutorialPage';

/**
 * Single entry for Unvalidated Redirect challenge (id 10).
 * Renders attack / fix / tutorial based on URL segment.
 */
const RedirectChallengePage: React.FC = () => {
  const { tab } = useParams<{ tab: string }>();

  if (tab === 'attack') return <RedirectAttackPage />;
  if (tab === 'fix') return <RedirectFixPage />;
  if (tab === 'tutorial') return <RedirectTutorialPage />;

  return <Navigate to="/challenges/10/tutorial" replace />;
};

export default RedirectChallengePage;
