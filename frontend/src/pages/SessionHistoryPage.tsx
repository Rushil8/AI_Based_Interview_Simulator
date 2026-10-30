import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { History, Calendar, ChevronRight, Play, Briefcase, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { SessionHistoryItem } from '../types';

export const SessionHistoryPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getUserInterviews(50, 0);
        setSessions(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load session history.');
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, []);

  const getScoreColor = (score?: number | null) => {
    if (score === undefined || score === null) return 'text-slate-600 bg-slate-100 border-slate-200';
    if (score >= 80) return 'text-green-800 bg-green-50 border-green-200';
    if (score >= 60) return 'text-blue-800 bg-blue-50 border-blue-200';
    return 'text-amber-800 bg-amber-50 border-amber-200';
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <History className="w-6 h-6 text-blue-600" />
            <span>Interview History</span>
          </h1>
          <p className="text-sm text-slate-600 mt-0.5">
            View your past practice sessions and score reports.
          </p>
        </div>

        <Link
          to="/setup"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors text-sm"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>New Session</span>
        </Link>
      </div>

      {loading ? (
        <div className="py-16 text-center">
          <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-slate-500 text-sm">Loading history...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      ) : sessions.length === 0 ? (
        <div className="bg-white p-8 rounded-xl border border-slate-200 text-center max-w-md mx-auto shadow-sm">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <Briefcase className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">No Practice Sessions Yet</h3>
          <p className="text-sm text-slate-600 mb-5 leading-relaxed">
            Upload your resume and choose a job role to begin your first interview practice session.
          </p>
          <Link
            to="/setup"
            className="inline-flex items-center space-x-1.5 px-5 py-2.5 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors text-sm"
          >
            <span>Start Practice</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((item) => (
            <div
              key={item.id}
              className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-base text-slate-900">{item.job_role}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 capitalize border border-slate-200">
                    {item.difficulty}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded border capitalize ${
                      item.status === 'completed'
                        ? 'text-green-800 bg-green-50 border-green-200'
                        : 'text-blue-800 bg-blue-50 border-blue-200'
                    }`}
                  >
                    {item.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-xs text-slate-500">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{new Date(item.started_at).toLocaleDateString()}</span>
                  </span>
                  <span>•</span>
                  <span>{item.target_question_count} Questions</span>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className={`text-base font-bold px-2.5 py-1 rounded-md border ${getScoreColor(item.overall_score)}`}>
                    {item.overall_score !== null && item.overall_score !== undefined
                      ? `${item.overall_score.toFixed(0)}/100`
                      : 'In Progress'}
                  </div>
                </div>

                {item.has_report ? (
                  <Link
                    to={`/interviews/${item.id}/report`}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors"
                  >
                    <span>View Report</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                ) : (
                  <Link
                    to={`/interviews/${item.id}`}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-colors"
                  >
                    <span>Resume</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
