import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';

// Import all pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardHomePage from './pages/DashboardHomePage';
import ChallengesListPage from './pages/ChallengesListPage';
import ScenarioPage from './pages/ScenarioPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import SqlInjectionAttackPage from './pages/SqlInjectionAttackPage';
import SqlInjectionFixPage from './pages/SqlInjectionFixPage';
import AttackSuccessPage from './pages/AttackSuccessPage';
import UnderConstructionPage from './pages/UnderConstructionPage'; // Import the new page

// Import layout
import MainLayout from './components/MainLayout';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* --- PUBLIC ROUTES --- */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* --- AUTHENTICATED ROUTES (Inside the sidebar layout) --- */}
        <Route element={<MainLayout />}>
          <Route path="/home" element={<DashboardHomePage />} />
          <Route path="/challenges" element={<ChallengesListPage />} />
          
          {/* Specific Challenge Routes */}
          <Route path="/challenges/1/attack" element={<SqlInjectionAttackPage />} />
          <Route path="/challenges/1/fix" element={<SqlInjectionFixPage />} />
          
          {/* Placeholder for other challenges */}
          <Route path="/challenges/:id" element={<ScenarioPage />} /> 

          {/* Result page */}
          <Route path="/challenges/attack-success" element={<AttackSuccessPage />} />
          
          {/* Under Construction Page Route */}
          <Route path="/under-construction" element={<UnderConstructionPage />} />

          {/* Admin Route */}
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        </Route>

        {/* Catch-all redirect for any unknown paths */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;