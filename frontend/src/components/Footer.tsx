import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Code2, BookOpen } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-slate-200 bg-white text-slate-600 py-10 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1 */}
          <div className="md:col-span-2">
            <span className="font-semibold text-base text-slate-900 flex items-center space-x-2 mb-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span>Technical Interview Coach</span>
            </span>
            <p className="text-sm text-slate-600 max-w-md leading-relaxed mb-3">
              A structured practice environment designed to help developers prepare for technical interviews
              through realistic question prompts, competency coverage checks, and standardized evaluation rubrics.
            </p>
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <ShieldCheck className="w-4 h-4 text-green-600" />
              <span>Resume processed securely in memory • No personal data retained</span>
            </div>
          </div>

          {/* Col 2 */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 mb-3">
              Navigation
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/" className="hover:text-blue-600 transition-colors">Overview</Link>
              </li>
              <li>
                <Link to="/setup" className="hover:text-blue-600 transition-colors">Start Interview</Link>
              </li>
              <li>
                <Link to="/history" className="hover:text-blue-600 transition-colors">Past Sessions</Link>
              </li>
              <li>
                <Link to="/settings" className="hover:text-blue-600 transition-colors">Settings & Privacy</Link>
              </li>
            </ul>
          </div>

          {/* Col 3 */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 mb-3">
              Scoring Rubric
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-600">
              <li>• Technical Correctness (40%)</li>
              <li>• Completeness & Depth (25%)</li>
              <li>• Relevance to Question (20%)</li>
              <li>• Communication Clarity (15%)</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <p>© 2026 Interview Coach. Educational practice tool.</p>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Code2 className="w-3.5 h-3.5 text-slate-400" />
              <span>FastAPI • Sentence-BERT • React</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
