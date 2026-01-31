import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';

// Import Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardHomePage from './pages/DashboardHomePage';
import ChallengesListPage from './pages/ChallengesListPage';
import SqlInjectionAttackPage from './pages/SqlInjectionAttackPage';
import SqlInjectionFixPage from './pages/SqlInjectionFixPage';
import SqlInjectionTutorialPage from './pages/SqlInjectionTutorialPage';
import AttackSuccessPage from './pages/AttackSuccessPage';
import UnderConstructionPage from './pages/UnderConstructionPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminStatsPage from './pages/AdminStatsPage'; // NEW
import InstructorDashboardPage from './pages/InstructorDashboardPage'; // NEW
import XssAttackPage from './pages/XssAttackPage';
import XssFixPage from './pages/XssFixPage';
import XssTutorialPage from './pages/XssTutorialPage';
import InstructorQuizPage from './pages/InstructorQuizPage';
import StudentQuizPage from './pages/StudentQuizPage';

// Components
import MainLayout from './components/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* --- PUBLIC ROUTES --- */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* --- STUDENT ROUTES --- */}
        <Route element={<ProtectedRoute allowedRoles={['user', 'instructor', 'admin']} />}>
          <Route element={<MainLayout />}>
            <Route path="/home" element={<DashboardHomePage />} />
            <Route path="/challenges" element={<ChallengesListPage />} />
            
            <Route path="/challenges/1/tutorial" element={<SqlInjectionTutorialPage />} />
            <Route path="/challenges/1/attack" element={<SqlInjectionAttackPage />} />
            <Route path="/challenges/1/fix" element={<SqlInjectionFixPage />} />
            
            <Route path="/challenges/2/tutorial" element={<XssTutorialPage />} />
            <Route path="/challenges/2/attack" element={<XssAttackPage />} />
            <Route path="/challenges/2/fix" element={<XssFixPage />} />
            
            <Route path="/challenges/attack-success" element={<AttackSuccessPage />} />
            <Route path="/quiz" element={<StudentQuizPage />} />
            <Route path="/under-construction" element={<UnderConstructionPage />} />
          </Route>
        </Route>

        {/* --- INSTRUCTOR ROUTES --- */}
        <Route element={<ProtectedRoute allowedRoles={['instructor', 'admin']} />}>
          <Route element={<MainLayout />}>
            <Route path="/instructor/dashboard" element={<InstructorDashboardPage />} /> {/* NEW DASHBOARD */}
            <Route path="/instructor/quiz" element={<InstructorQuizPage />} />
          </Route>
        </Route>

        {/* --- ADMIN ROUTES --- */}
        <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
          <Route element={<MainLayout />}>
            <Route path="/admin/stats" element={<AdminStatsPage />} /> {/* NEW VISUAL DASHBOARD */}
            <Route path="/admin/dashboard" element={<AdminDashboardPage />} /> {/* USER MANAGEMENT */}
            <Route path="/admin/logs" element={<UnderConstructionPage />} />
          </Route>
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;