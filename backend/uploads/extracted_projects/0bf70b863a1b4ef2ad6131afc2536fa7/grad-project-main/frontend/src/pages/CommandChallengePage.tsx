import * as React from 'react';
import { useParams, Navigate } from 'react-router-dom';
import CommandInjectionAttackPage from './CommandInjectionAttackPage';
import CommandInjectionFixPage from './CommandInjectionFixPage';
import CommandInjectionTutorialPage from './CommandInjectionTutorialPage';

/** Single entry for Command Injection challenge (id 4). */
const CommandChallengePage: React.FC = () => {
  const { tab } = useParams<{ tab: string }>();

  if (tab === 'attack') return <CommandInjectionAttackPage />;
  if (tab === 'fix') return <CommandInjectionFixPage />;
  if (tab === 'tutorial') return <CommandInjectionTutorialPage />;

  return <Navigate to="/challenges/4/tutorial" replace />;
};

export default CommandChallengePage;
