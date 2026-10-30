import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { ResumeUploadPage } from './pages/ResumeUploadPage';
import { ProfileReviewPage } from './pages/ProfileReviewPage';
import { InterviewDashboardPage } from './pages/InterviewDashboardPage';
import { FinalReportPage } from './pages/FinalReportPage';
import { SessionHistoryPage } from './pages/SessionHistoryPage';
import { SettingsPrivacyPage } from './pages/SettingsPrivacyPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/setup" element={<ResumeUploadPage />} />
            <Route path="/profiles/:id/review" element={<ProfileReviewPage />} />
            <Route path="/interviews/:sessionId" element={<InterviewDashboardPage />} />
            <Route path="/interviews/:sessionId/report" element={<FinalReportPage />} />
            <Route path="/history" element={<SessionHistoryPage />} />
            <Route path="/settings" element={<SettingsPrivacyPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
};

export default App;
