import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './store/auth';
import { ClientProvider } from './store/clients';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import AccountRequest from './pages/AccountRequest';
import Profile from './pages/Profile';
import DashboardShell from './components/DashboardShell';
import ErrorBoundary from './components/ErrorBoundary';
import NotificationSystem from './components/NotificationSystem';
import SessionWarningModal from './components/SessionWarningModal';

// Pages
import HRDashboard from './pages/hr/Dashboard';
import Jobs from './pages/hr/Jobs';
import ResumeUpload from './pages/hr/ResumeUpload';
import ResumeList from './pages/hr/ResumeList';
import JDManager from './pages/hr/JDManager';
import ParsedProfiles from './pages/hr/ParsedProfiles';
import InboxLink from './pages/hr/InboxLink';
import OfferLetters from './pages/hr/OfferLetters';
import SignedOfferLetters from './pages/hr/SignedOfferLetters';
import ClientSubmit from './pages/hr/ClientSubmit';
import ClientDetail from './pages/hr/ClientDetail';
import ClientDashboard from './pages/hr/ClientDashboard';
import CandidateOnboarding from './pages/hr/CandidateOnboarding';
import Invoice from './pages/hr/Invoice';
import Ledger from './pages/hr/Ledger';
import Expenses from './pages/hr/Expenses';
import ManagerDashboard from './pages/manager/Dashboard';
import SharedResumes from './pages/manager/SharedResumes';
import AdminDashboard from './pages/admin/Dashboard';
import AdminUsers from './pages/admin/Users';
import AdminServices from './pages/admin/Services';
import SuperadminDashboard from './pages/superadmin/Dashboard';
import SuperadminAdmins from './pages/superadmin/Admins';
import CandidateOnboardingForm from './pages/CandidateOnboardingForm';
import OnboardingSuccess from './pages/OnboardingSuccess';
import OfferSignature from './pages/public/OfferSignature';
import MSA from './pages/hr/MSA';
import MSASignature from './pages/public/MSASignature';
import MSASuccess from './pages/MSASuccess';

function App() {
  const { isAuthenticated, user, loading, showSessionWarning, sessionTimeLeft, extendSession, logout } = useAuth();

  console.log('App render - isAuthenticated:', isAuthenticated, 'user:', user, 'loading:', loading);
  
  // Debug: Log when authentication state changes
  React.useEffect(() => {
    console.log('App useEffect - Auth state changed:', { isAuthenticated, user, loading });
  }, [isAuthenticated, user, loading]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-modern">
        <div className="text-center">
          <div className="spinner w-8 h-8 border-4 border-white border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-white font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/account-request" element={<AccountRequest />} />
          <Route path="/candidate-onboarding/:token" element={<CandidateOnboardingForm />} />
          <Route path="/onboarding-success" element={<OnboardingSuccess />} />
          <Route path="/offer-sign/:token" element={<OfferSignature />} />
          <Route path="/msa-sign/:token" element={<MSASignature />} />
          <Route path="/msa-success" element={<MSASuccess />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <ClientProvider>
        <NotificationSystem />
        <SessionWarningModal 
          isOpen={showSessionWarning}
          timeLeft={sessionTimeLeft}
          onExtendSession={extendSession}
          onLogout={logout}
        />
        <Routes>
          {/* Public routes accessible even when logged in (for external users) */}
          <Route path="/candidate-onboarding/:token" element={<CandidateOnboardingForm />} />
          <Route path="/onboarding-success" element={<OnboardingSuccess />} />
          <Route path="/offer-sign/:token" element={<OfferSignature />} />
          <Route path="/msa-sign/:token" element={<MSASignature />} />
          <Route path="/msa-success" element={<MSASuccess />} />
          <Route path="/" element={<DashboardShell />}>
        {/* Superadmin Routes */}
        {user?.role === 'superadmin' && (
          <>
            <Route index element={<Navigate to="/superadmin/dashboard" replace />} />
            <Route path="superadmin/dashboard" element={<SuperadminDashboard />} />
            <Route path="superadmin/admins" element={<SuperadminAdmins />} />
          </>
        )}

        {/* Admin Routes - Admins have access to all HR features + User Management */}
        {user?.role === 'admin' && (
          <>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="admin/dashboard" element={<AdminDashboard />} />
            <Route path="admin/users" element={<AdminUsers />} />
            <Route path="admin/services" element={<AdminServices />} />
            <Route path="hr/dashboard" element={<HRDashboard />} />
            <Route path="hr/jobs" element={<Jobs />} />
            <Route path="hr/upload" element={<ResumeUpload />} />
            <Route path="hr/resumes" element={<ResumeList />} />
            <Route path="hr/jd-manager" element={<JDManager />} />
            <Route path="hr/parsed-profiles" element={<ParsedProfiles />} />
            <Route path="hr/inbox-link" element={<InboxLink />} />
            <Route path="hr/offer-letters" element={<OfferLetters />} />
            <Route path="hr/signed-offer-letters" element={<SignedOfferLetters />} />
            <Route path="hr/client-submit" element={<ClientSubmit />} />
            <Route path="hr/clients" element={<ClientDashboard />} />
            <Route path="hr/clients/:id" element={<ClientDetail />} />
            <Route path="hr/msa" element={<MSA />} />
            <Route path="hr/candidate-onboarding" element={<CandidateOnboarding />} />
            <Route path="hr/invoice" element={<Invoice />} />
            <Route path="hr/ledger" element={<Ledger />} />
            <Route path="hr/expenses" element={<Expenses />} />
          </>
        )}

        {/* HR Routes */}
        {user?.role === 'hr' && (
          <>
            <Route index element={<Navigate to="/hr/dashboard" replace />} />
            <Route path="hr/dashboard" element={<HRDashboard />} />
            <Route path="hr/jobs" element={<Jobs />} />
            <Route path="hr/upload" element={<ResumeUpload />} />
            <Route path="hr/resumes" element={<ResumeList />} />
            <Route path="hr/jd-manager" element={<JDManager />} />
            <Route path="hr/parsed-profiles" element={<ParsedProfiles />} />
            <Route path="hr/inbox-link" element={<InboxLink />} />
            <Route path="hr/offer-letters" element={<OfferLetters />} />
            <Route path="hr/signed-offer-letters" element={<SignedOfferLetters />} />
            <Route path="hr/client-submit" element={<ClientSubmit />} />
            <Route path="hr/clients" element={<ClientDashboard />} />
            <Route path="hr/clients/:id" element={<ClientDetail />} />
            <Route path="hr/msa" element={<MSA />} />
            <Route path="hr/candidate-onboarding" element={<CandidateOnboarding />} />
          </>
        )}

        {/* Manager Routes */}
        {user?.role === 'manager' && (
          <>
            <Route index element={<Navigate to="/manager/dashboard" replace />} />
            <Route path="manager/dashboard" element={<ManagerDashboard />} />
            <Route path="manager/shared-resumes" element={<SharedResumes />} />
          </>
        )}

        {/* Accountant Routes */}
        {user?.role === 'accountant' && (
          <>
            <Route index element={<Navigate to="/hr/invoice" replace />} />
            <Route path="hr/invoice" element={<Invoice />} />
            <Route path="hr/ledger" element={<Ledger />} />
            <Route path="hr/expenses" element={<Expenses />} />
            <Route path="hr/msa" element={<MSA />} />
          </>
        )}

        {/* Common Routes */}
        <Route path="profile" element={<Profile />} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
      </ClientProvider>
    </ErrorBoundary>
  );
}

export default App;
