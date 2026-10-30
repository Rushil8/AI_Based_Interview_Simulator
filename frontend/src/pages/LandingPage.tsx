import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Sliders
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12 sm:py-16">
      {/* HERO */}
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 mb-4 leading-tight">
          Practice Technical Interviews with Objective Feedback
        </h1>

        <p className="text-base text-slate-600 mb-8 leading-relaxed">
          Select your target role, answer scenario-based technical questions, and receive detailed scoring based on factual correctness, depth, and clarity.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-12">
          <Link
            to="/setup"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-2.5 rounded-lg font-medium text-sm bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors"
          >
            <span>Start Practice Interview</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <Link
            to="/settings"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-lg font-medium text-sm bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors"
          >
            <Sliders className="w-4 h-4 text-slate-500" />
            <span>How Scoring Works</span>
          </Link>
        </div>
      </div>

      {/* 3-STEP QUICK OVERVIEW */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-8 h-8 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs mb-3">
            1
          </div>
          <h3 className="font-semibold text-sm text-slate-900 mb-1">Select Role & Resume</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Pick your target job role. Optionally upload a PDF resume or use a sample profile in one click.
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-8 h-8 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs mb-3">
            2
          </div>
          <h3 className="font-semibold text-sm text-slate-900 mb-1">Answer Questions</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Respond to technical prompts with your reasoning. Difficulty adjusts adaptively based on answers.
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-8 h-8 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs mb-3">
            3
          </div>
          <h3 className="font-semibold text-sm text-slate-900 mb-1">Get Rubric Feedback</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Review detailed scores across Technical (40%), Completeness (25%), Relevance (20%), and Clarity (15%).
          </p>
        </div>
      </div>

      {/* RUBRIC PILLS SUMMARY */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="font-semibold text-sm text-slate-900">Standardized Scoring Rubric</h4>
          <p className="text-xs text-slate-500 mt-0.5">Every response is graded against fixed, transparent evaluation criteria.</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 font-medium">Technical: 40%</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 font-medium">Completeness: 25%</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 font-medium">Relevance: 20%</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 font-medium">Clarity: 15%</span>
        </div>
      </div>
    </div>
  );
};
