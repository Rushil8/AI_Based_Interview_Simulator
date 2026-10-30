import React, { useState } from 'react';
import {
  ShieldCheck,
  Sliders,
  Trash2,
  CheckCircle2,
  Lock
} from 'lucide-react';

const RUBRIC_ITEMS = [
  {
    name: 'Technical Correctness',
    weight: '40%',
    description: 'Accurate technical concepts, proper patterns, and awareness of architectural constraints.',
    color: 'text-blue-700 bg-blue-50 border-blue-200'
  },
  {
    name: 'Completeness & Depth',
    weight: '25%',
    description: 'Detailed coverage of mechanisms, trade-offs, and practical edge cases.',
    color: 'text-slate-700 bg-slate-100 border-slate-200'
  },
  {
    name: 'Relevance to Question',
    weight: '20%',
    description: 'Directly answering the specific prompt without unnecessary tangents or buzzwords.',
    color: 'text-slate-700 bg-slate-100 border-slate-200'
  },
  {
    name: 'Communication & Clarity',
    weight: '15%',
    description: 'Structured, concise, and easy-to-follow explanations.',
    color: 'text-slate-700 bg-slate-100 border-slate-200'
  },
];

export const SettingsPrivacyPage: React.FC = () => {
  const [cleared, setCleared] = useState<boolean>(false);

  const handleClearLocalSession = () => {
    sessionStorage.clear();
    localStorage.clear();
    setCleared(true);
    setTimeout(() => setCleared(false), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* HEADER */}
      <div className="pb-3 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Scoring & Privacy
        </h1>
        <p className="text-sm text-slate-600 mt-0.5">
          How your answers are evaluated and how your data is handled.
        </p>
      </div>

      {cleared && (
        <div className="p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-green-600" />
          <span>Local session storage cleared successfully.</span>
        </div>
      )}

      {/* RUBRIC EXPLANATION */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm font-semibold text-slate-900">
            <Sliders className="w-4 h-4 text-blue-600" />
            <span>How Answers Are Graded</span>
          </div>
          <span className="text-xs text-slate-500 font-medium">Standard 4-Part Rubric</span>
        </div>

        <div className="space-y-2.5">
          {RUBRIC_ITEMS.map((item) => (
            <div
              key={item.name}
              className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
            >
              <div>
                <div className="font-semibold text-sm text-slate-900">{item.name}</div>
                <div className="text-xs text-slate-600 mt-0.5">{item.description}</div>
              </div>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-md border shrink-0 ${item.color}`}>
                {item.weight}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* PRIVACY PROMISE */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center space-x-2 text-sm font-semibold text-slate-900">
          <Lock className="w-4 h-4 text-green-600" />
          <span>Privacy & Data Handling</span>
        </div>

        <div className="space-y-2 text-xs text-slate-600 leading-relaxed">
          <div className="flex items-start space-x-2">
            <ShieldCheck className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
            <span><strong>Private to you:</strong> Your resume and responses are used only to generate relevant interview questions and are never shared or sold.</span>
          </div>
          <div className="flex items-start space-x-2">
            <ShieldCheck className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
            <span><strong>No model training:</strong> Your typed answers are not used to train public machine learning models.</span>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-500">Reset local browser data</span>
          <button
            type="button"
            onClick={handleClearLocalSession}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-medium transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Local History</span>
          </button>
        </div>
      </div>
    </div>
  );
};
