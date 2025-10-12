import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChallengesListPage from './pages/ChallengesListPage';
import ScenarioPage from './pages/ScenarioPage';
import MainLayout from './components/MainLayout';
import SqlInjectionAttackPage from './pages/SqlInjectionAttackPage'; // 1. Import attack page
import AttackSuccessPage from './pages/AttackSuccessPage'; // 2. Import success page

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        <Route element={<MainLayout />}>
          <Route path="/challenges" element={<ChallengesListPage />} />
          <Route path="/challenges/:id" element={<ScenarioPage />} />
          
          {/* 3. Add the new routes */}
          <Route path="/challenges/1/attack" element={<SqlInjectionAttackPage />} />
          <Route path="/challenges/attack-success" element={<AttackSuccessPage />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;