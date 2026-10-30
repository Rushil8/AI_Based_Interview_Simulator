import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, History, HelpCircle, Play } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/setup', label: 'Practice', icon: Play },
    { to: '/history', label: 'History', icon: History },
    { to: '/settings', label: 'Scoring & Privacy', icon: HelpCircle },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-md bg-blue-600 text-white flex items-center justify-center">
            <FileText className="w-4 h-4" />
          </div>
          <span className="font-semibold text-base text-slate-900 tracking-tight">
            Interview Coach
          </span>
        </Link>

        {/* Navigation links */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-slate-100 text-slate-900 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Quick Start button */}
        {location.pathname !== '/setup' && (
          <Link
            to="/setup"
            className="hidden sm:inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Start Practice</span>
          </Link>
        )}
      </div>
    </header>
  );
};
