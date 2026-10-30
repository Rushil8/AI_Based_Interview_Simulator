import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  Briefcase,
  Sliders,
  CheckCircle,
  FileCode2,
  ArrowRight,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';

const ROLE_PRESETS = [
  'Full Stack Engineer',
  'Backend Developer',
  'Frontend Developer',
  'Data Scientist / ML',
  'DevOps Engineer',
];

export const ResumeUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [jobRole, setJobRole] = useState<string>('Full Stack Engineer');
  const [customRole, setCustomRole] = useState<string>('');
  const [difficulty, setDifficulty] = useState<string>('mid');
  const [questionCount, setQuestionCount] = useState<number>(5);

  const [loading, setLoading] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF document (.pdf).');
      return;
    }
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be under 10MB.');
      return;
    }
    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const getOrCreateResumeFile = async (): Promise<File> => {
    if (file) return file;
    // Generate sample PDF if user hasn't uploaded one
    const response = await fetch('/sample_resume.pdf').catch(() => null);
    let sampleBlob: Blob;
    if (response && response.ok) {
      sampleBlob = await response.blob();
    } else {
      sampleBlob = new Blob([
        `%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000106 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n180\n%%EOF`
      ], { type: 'application/pdf' });
    }
    return new File([sampleBlob], 'Sample_Resume.pdf', { type: 'application/pdf' });
  };

  const handleUseSampleResume = async () => {
    try {
      const sampleFile = await getOrCreateResumeFile();
      setFile(sampleFile);
    } catch {
      setError('Could not prepare sample resume.');
    }
  };

  const handleStartInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalRole = jobRole === 'Custom' ? customRole.trim() : jobRole;
    if (!finalRole) {
      setError('Please choose or enter a target job role.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      setLoadingStep('Processing resume...');
      const resumeFileToUse = await getOrCreateResumeFile();
      const profile = await api.uploadResume(resumeFileToUse);

      setLoadingStep('Generating tailored questions...');
      const session = await api.createInterview({
        profile_id: profile.id,
        job_role: finalRole,
        difficulty,
        duration_minutes: questionCount === 3 ? 15 : questionCount === 5 ? 30 : 45,
        target_question_count: questionCount,
      });

      navigate(`/interviews/${session.id}`);
    } catch (err: any) {
      setError(err.message || 'Could not start interview. Please ensure backend is running.');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Start a Practice Interview
        </h1>
        <p className="text-sm text-slate-600 mt-0.5">
          Choose your role, upload a resume (or use a sample), and begin practicing.
        </p>
      </div>

      {error && (
        <div className="mb-5 p-3.5 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start space-x-2 text-sm">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleStartInterview} className="space-y-5">
        {/* ROLE SELECTION */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <label className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
            <Briefcase className="w-4 h-4 text-blue-600" />
            <span>1. Target Role</span>
          </label>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {ROLE_PRESETS.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => {
                  setJobRole(preset);
                  setCustomRole('');
                }}
                className={`px-3 py-2 rounded-lg text-xs font-medium text-left border transition-colors ${
                  jobRole === preset
                    ? 'border-blue-600 bg-blue-50 text-blue-900 font-semibold ring-1 ring-blue-600'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                {preset}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setJobRole('Custom')}
              className={`px-3 py-2 rounded-lg text-xs font-medium text-left border transition-colors ${
                jobRole === 'Custom'
                  ? 'border-blue-600 bg-blue-50 text-blue-900 font-semibold ring-1 ring-blue-600'
                  : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              Other Role...
            </button>
          </div>

          {jobRole === 'Custom' && (
            <input
              type="text"
              value={customRole}
              onChange={(e) => setCustomRole(e.target.value)}
              placeholder="e.g. iOS Developer, Cloud Architect"
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          )}
        </div>

        {/* RESUME UPLOAD */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <span>2. Resume</span>
            </label>
            <button
              type="button"
              onClick={handleUseSampleResume}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center space-x-1"
            >
              <FileCode2 className="w-3.5 h-3.5" />
              <span>Use sample resume</span>
            </button>
          </div>

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-5 text-center cursor-pointer transition-colors ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : file
                ? 'border-green-400 bg-green-50/40'
                : 'border-slate-300 hover:border-slate-400 bg-slate-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileInput}
              className="hidden"
            />

            {file ? (
              <div className="flex items-center justify-center space-x-2 text-sm text-slate-800">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="font-medium">{file.name}</span>
                <span className="text-xs text-slate-500">({(file.size / 1024).toFixed(0)} KB)</span>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-5 h-5 text-slate-400 mb-1" />
                <span className="text-xs font-medium text-slate-700">
                  Drop PDF here or click to browse
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5">
                  Optional: If skipped, a standard profile will be used automatically
                </span>
              </div>
            )}
          </div>
        </div>

        {/* SETTINGS */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <label className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-blue-600" />
            <span>3. Questions & Level</span>
          </label>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="block text-xs font-medium text-slate-600 mb-1.5">Experience Level</span>
              <div className="flex rounded-lg p-1 bg-slate-100 border border-slate-200">
                {['junior', 'mid', 'senior'].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setDifficulty(lvl)}
                    className={`flex-1 py-1 rounded-md text-xs font-medium capitalize transition-colors ${
                      difficulty === lvl
                        ? 'bg-white text-slate-900 font-semibold shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {lvl === 'mid' ? 'Mid-level' : lvl}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <span className="block text-xs font-medium text-slate-600 mb-1.5">Question Count</span>
              <div className="flex rounded-lg p-1 bg-slate-100 border border-slate-200">
                {[3, 5, 8].map((count) => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setQuestionCount(count)}
                    className={`flex-1 py-1 rounded-md text-xs font-medium transition-colors ${
                      questionCount === count
                        ? 'bg-white text-slate-900 font-semibold shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {count} Questions
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* START BUTTON */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 py-3 rounded-lg font-medium text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>{loadingStep || 'Preparing session...'}</span>
              </>
            ) : (
              <>
                <span>Start Practice Interview</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
