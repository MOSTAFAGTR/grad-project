import * as React from 'react';
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
import MessagesPage from './pages/MessagesPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminStatsPage from './pages/AdminStatsPage'; // NEW
import InstructorDashboardPage from './pages/InstructorDashboardPage'; // NEW
import XssAttackPage from './pages/XssAttackPage';
import XssFixPage from './pages/XssFixPage';
import XssTutorialPage from './pages/XssTutorialPage';
import InstructorQuizPage from './pages/InstructorQuizPage';
import StudentQuizPage from './pages/StudentQuizPage';
import CsrfAttackPage from './pages/CsrfAttackPage';
import CsrfFixPage from './pages/CsrfFixPage';
import CsrfTutorialPage from './pages/CsrfTutorialPage';
import RedirectChallengePage from './pages/RedirectChallengePage';
import CommandChallengePage from './pages/CommandChallengePage';
import BrokenAuthAttackPage from './pages/BrokenAuthAttackPage';
import BrokenAuthFixPage from './pages/BrokenAuthFixPage';
import SecurityMiscAttackPage from './pages/SecurityMiscAttackPage';
import SecurityMiscFixPage from './pages/SecurityMiscFixPage';
import Scanner from './pages/Scanner';
import AttackLab from './pages/AttackLab';
import SecurityLogsPage from './pages/SecurityLogsPage';
import InsecureStorageChallengePage from './pages/InsecureStorageChallengePage';
import DirectoryTraversalChallengePage from './pages/DirectoryTraversalChallengePage';
import XxeChallengePage from './pages/XxeChallengePage';

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
            <Route path="/messages" element={<MessagesPage />} />
            <Route path="/scanner" element={<Scanner />} />
            <Route path="/attack-lab" element={<AttackLab />} />
            
            <Route path="/challenges/1/tutorial" element={<SqlInjectionTutorialPage />} />
            <Route path="/challenges/1/attack" element={<SqlInjectionAttackPage />} />
            <Route path="/challenges/1/fix" element={<SqlInjectionFixPage />} />
            
            <Route path="/challenges/2/tutorial" element={<XssTutorialPage />} />
            <Route path="/challenges/2/attack" element={<XssAttackPage />} />
            <Route path="/challenges/2/fix" element={<XssFixPage />} />

            <Route path="/challenges/3/attack" element={<CsrfAttackPage />} />
            <Route path="/challenges/3/fix" element={<CsrfFixPage />} />
            <Route path="/challenges/3/tutorial" element={<CsrfTutorialPage />} />

            {/* Command Injection (challenge 4) */}
            <Route path="/challenges/4/:tab" element={<CommandChallengePage />} />

            <Route path="/challenges/5/attack" element={<BrokenAuthAttackPage />} />
            <Route path="/challenges/5/fix" element={<BrokenAuthFixPage />} />

            <Route path="/challenges/6/attack" element={<SecurityMiscAttackPage />} />
            <Route path="/challenges/6/fix" element={<SecurityMiscFixPage />} />
            <Route path="/challenges/7/:tab" element={<InsecureStorageChallengePage />} />
            <Route path="/challenges/8/:tab" element={<DirectoryTraversalChallengePage />} />
            <Route path="/challenges/9/:tab" element={<XxeChallengePage />} />
            

            {/* Unvalidated Redirect (challenge 10): /challenges/10/attack | fix | tutorial */}
            <Route path="/challenges/10/:tab" element={<RedirectChallengePage />} />

            <Route path="/challenges/attack-success" element={<AttackSuccessPage />} />
            <Route element={<ProtectedRoute allowedRoles={['user']} />}>
              <Route path="/quiz" element={<StudentQuizPage />} />
            </Route>
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
            <Route path="/admin/logs" element={<SecurityLogsPage />} />
          </Route>
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;