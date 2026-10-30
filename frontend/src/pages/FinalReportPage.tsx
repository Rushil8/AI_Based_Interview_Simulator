import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BarChart3,
  CheckCircle2,
  Printer,
  RotateCcw,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Layers,
  HelpCircle
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { SessionReportResponse } from '../types';

export const FinalReportPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();

  const [report, setReport] = useState<SessionReportResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    const fetchReport = async () => {
      setLoading(true);
      setLoadError(null);
      try {
        const data = await api.getSessionReport(sessionId);
        setReport(data);
      } catch (err: any) {
        setLoadError(err.message || 'Failed to load session report.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [sessionId]);

  const toggleQuestion = (seq: number) => {
    setExpandedQuestion(expandedQuestion === seq ? null : seq);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-600 font-medium text-sm">Generating performance report...</p>
      </div>
    );
  }

  if (loadError || !report) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <p className="text-red-600 font-medium">{loadError || 'Report not found.'}</p>
        <Link to="/" className="mt-3 inline-block text-blue-600 underline text-sm">
          Return to Home
        </Link>
      </div>
    );
  }

  // Chart data formatting
  const competencyChartData = report.competency_scores.map((c) => ({
    name: c.name.length > 20 ? c.name.substring(0, 18) + '...' : c.name,
    fullName: c.name,
    score: c.score,
    tested: c.questions_tested,
  }));

  const dimensionChartData = [
    { name: 'Technical (40%)', score: report.dimension_scores.technical_correctness, color: '#2563eb' },
    { name: 'Completeness (25%)', score: report.dimension_scores.completeness, color: '#475569' },
    { name: 'Relevance (20%)', score: report.dimension_scores.relevance, color: '#0284c7' },
    { name: 'Communication (15%)', score: report.dimension_scores.communication, color: '#16a34a' },
  ];

  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'text-green-800 bg-green-50 border-green-200';
    if (score >= 60) return 'text-blue-800 bg-blue-50 border-blue-200';
    return 'text-amber-800 bg-amber-50 border-amber-200';
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* HEADER & ACTIONS */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-5 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center space-x-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200 mb-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Interview Complete</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Performance Summary & Report
          </h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Target Role: <strong className="text-slate-800">{report.job_role}</strong> • Completed {new Date(report.generated_at).toLocaleDateString()}
          </p>
        </div>

        <div className="flex items-center space-x-2 print:hidden">
          <button
            type="button"
            onClick={() => window.print()}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 bg-white text-slate-700 text-sm font-medium transition-colors"
          >
            <Printer className="w-4 h-4 text-slate-500" />
            <span>Print Report</span>
          </button>

          <Link
            to="/setup"
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors text-sm"
          >
            <RotateCcw className="w-4 h-4" />
            <span>New Practice Session</span>
          </Link>
        </div>
      </div>

      {/* OVERALL SCORE & SUMMARY (NO RADIAL CHARTS) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Score Box - Simple, clean, no radial/gradient */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
            Overall Score
          </span>

          <div className="my-3">
            <span className="text-5xl font-bold text-slate-900">
              {report.overall_score.toFixed(0)}
            </span>
            <span className="text-base text-slate-500 font-medium"> / 100</span>
          </div>

          <div className={`mt-2 px-3 py-1 rounded-full text-xs font-semibold border ${getScoreBadgeColor(report.overall_score)}`}>
            {report.overall_score >= 80 ? 'Exceeds Expectations' : report.overall_score >= 60 ? 'Meets Expectations' : 'Needs Development'}
          </div>

          <p className="text-xs text-slate-500 mt-4">
            Evaluated on standard 4-dimension technical rubric
          </p>
        </div>

        {/* Performance Summary & Stats */}
        <div className="md:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-blue-700 mb-1.5">
              Summary
            </div>
            <p className="text-sm text-slate-700 leading-relaxed font-normal mb-5">
              {report.performance_summary}
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-100 text-xs">
            <div>
              <span className="text-slate-500 block mb-0.5">Questions Answered</span>
              <span className="text-base font-bold text-slate-900">{report.answered_count}</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-0.5">Competency Coverage</span>
              <span className="text-base font-bold text-slate-900">{report.coverage_pct.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-0.5">Top Area</span>
              <span className="text-xs font-semibold text-slate-800 truncate block">
                {report.strongest_competencies[0] || 'Core Engineering'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-0.5">Area for Growth</span>
              <span className="text-xs font-semibold text-amber-800 truncate block">
                {report.weakest_competencies[0] || 'System Design'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 4 DIMENSIONS & COMPETENCY CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dimension Breakdown Bar Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>Rubric Breakdown</span>
            </h3>
            <span className="text-xs text-slate-500">Scale: 0 - 100</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dimensionChartData} layout="vertical" margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fill: '#334155', fontSize: 11 }} width={120} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                  formatter={(val: any) => [`${Number(val).toFixed(0)}%`, 'Score']}
                />
                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                  {dimensionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Competencies Tested Bar Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-slate-700" />
              <span>Competency Breakdown</span>
            </h3>
            <span className="text-xs text-slate-500">By Domain</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={competencyChartData} margin={{ left: 0, right: 20, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 10 }} interval={0} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                  formatter={(val: any, _name: any, item: any) => [`${Number(val).toFixed(0)}%`, item.payload.fullName]}
                />
                <Bar dataKey="score" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ACTIONABLE IMPROVEMENT PLAN */}
      <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-200">
          Key Feedback & Revision Plan
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Key Strengths */}
          <div className="p-4 rounded-lg bg-green-50 border border-green-200 space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-green-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <span>What You Did Well</span>
            </span>
            <ul className="space-y-1.5 text-xs text-green-900 list-disc list-inside">
              {report.feedback.overall_strengths.map((str, idx) => (
                <li key={idx}>{str}</li>
              ))}
            </ul>
          </div>

          {/* Missing Concepts & Next Steps */}
          <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-800 flex items-center space-x-1.5">
              <HelpCircle className="w-4 h-4 text-amber-600" />
              <span>Topics to Review</span>
            </span>
            <ul className="space-y-1.5 text-xs text-amber-900 list-disc list-inside">
              {report.feedback.missing_concepts.map((concept, idx) => (
                <li key={idx}>{concept}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* QUESTION BY QUESTION ACCORDION REVIEW */}
      <div className="space-y-3">
        <h3 className="text-base font-bold text-slate-900">
          Question Review ({report.question_reviews.length})
        </h3>

        {report.question_reviews.map((qr) => (
          <div
            key={qr.sequence_number}
            className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
          >
            <button
              type="button"
              onClick={() => toggleQuestion(qr.sequence_number)}
              className="w-full p-4 text-left flex items-center justify-between hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <span className="w-7 h-7 rounded-md bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center">
                  Q{qr.sequence_number}
                </span>
                <div>
                  <div className="font-semibold text-sm text-slate-900">{qr.question_text}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {qr.competency_name} • <span className="capitalize">{qr.difficulty}</span> difficulty
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${getScoreBadgeColor(qr.weighted_score)}`}>
                  {qr.weighted_score.toFixed(0)}/100
                </span>
                {expandedQuestion === qr.sequence_number ? (
                  <ChevronUp className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                )}
              </div>
            </button>

            {expandedQuestion === qr.sequence_number && (
              <div className="p-4 border-t border-slate-200 bg-slate-50 space-y-3 text-xs">
                {/* Candidate Answer */}
                <div>
                  <span className="font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                    Your Answer:
                  </span>
                  <div className="p-3 rounded-lg bg-white border border-slate-200 text-slate-800 leading-relaxed font-mono whitespace-pre-wrap">
                    {qr.answer_text}
                  </div>
                </div>

                {/* Dimension scores pill row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                    <span className="text-slate-500 block">Technical (40%)</span>
                    <strong className="text-blue-700 text-sm">{qr.technical_score.toFixed(0)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                    <span className="text-slate-500 block">Completeness (25%)</span>
                    <strong className="text-slate-800 text-sm">{qr.completeness_score.toFixed(0)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                    <span className="text-slate-500 block">Relevance (20%)</span>
                    <strong className="text-slate-800 text-sm">{qr.relevance_score.toFixed(0)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                    <span className="text-slate-500 block">Communication (15%)</span>
                    <strong className="text-slate-800 text-sm">{qr.communication_score.toFixed(0)}%</strong>
                  </div>
                </div>

                {/* Concepts identified & suggestions */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                  {qr.correct_concepts.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-green-50 border border-green-200 text-green-900">
                      <strong className="text-green-800 block mb-0.5">Correct Concepts:</strong>
                      {qr.correct_concepts.join(' • ')}
                    </div>
                  )}
                  {qr.missing_concepts.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">
                      <strong className="text-amber-800 block mb-0.5">Missing Points:</strong>
                      {qr.missing_concepts.join(' • ')}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* HIRING DISCLAIMER BANNER */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-600 text-xs flex items-start space-x-3">
        <ShieldAlert className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="text-slate-800">Practice Notice:</strong> {report.hiring_disclaimer}
        </div>
      </div>
    </div>
  );
};
