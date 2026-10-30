import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  User,
  Briefcase,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Plus,
  X,
  Target,
  Save,
  Layers
} from 'lucide-react';
import { api } from '../services/api';
import { StructuredProfile } from '../types';

export const ProfileReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<StructuredProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [startingInterview, setStartingInterview] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  // New skill input states
  const [newSkill, setNewSkill] = useState<string>('');
  const [skillCategory, setSkillCategory] = useState<'languages' | 'frameworks' | 'tools'>('languages');

  // Load setup params from sessionStorage
  const setupParams = JSON.parse(sessionStorage.getItem('interview_setup') || '{}');
  const jobRole = setupParams.job_role || 'Full Stack Engineer';

  useEffect(() => {
    if (!id) return;
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getProfile(id);
        setProfile(res.structured_profile);
      } catch (err: any) {
        setError(err.message || 'Failed to load profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [id]);

  const handleProfileFieldChange = (field: keyof StructuredProfile, value: any) => {
    if (!profile) return;
    setProfile({ ...profile, [field]: value });
  };

  const handleAddSkill = () => {
    if (!newSkill.trim() || !profile) return;
    const term = newSkill.trim();

    if (skillCategory === 'languages') {
      if (!profile.programming_languages.includes(term)) {
        setProfile({
          ...profile,
          programming_languages: [...profile.programming_languages, term],
          technical_skills: [...profile.technical_skills, term],
        });
      }
    } else if (skillCategory === 'frameworks') {
      if (!profile.frameworks_libraries.includes(term)) {
        setProfile({
          ...profile,
          frameworks_libraries: [...profile.frameworks_libraries, term],
          technical_skills: [...profile.technical_skills, term],
        });
      }
    } else {
      if (!profile.tools_platforms.includes(term)) {
        setProfile({
          ...profile,
          tools_platforms: [...profile.tools_platforms, term],
          technical_skills: [...profile.technical_skills, term],
        });
      }
    }
    setNewSkill('');
  };

  const handleRemoveSkill = (category: 'languages' | 'frameworks' | 'tools', skillToRemove: string) => {
    if (!profile) return;
    if (category === 'languages') {
      setProfile({
        ...profile,
        programming_languages: profile.programming_languages.filter((s) => s !== skillToRemove),
        technical_skills: profile.technical_skills.filter((s) => s !== skillToRemove),
      });
    } else if (category === 'frameworks') {
      setProfile({
        ...profile,
        frameworks_libraries: profile.frameworks_libraries.filter((s) => s !== skillToRemove),
        technical_skills: profile.technical_skills.filter((s) => s !== skillToRemove),
      });
    } else {
      setProfile({
        ...profile,
        tools_platforms: profile.tools_platforms.filter((s) => s !== skillToRemove),
        technical_skills: profile.technical_skills.filter((s) => s !== skillToRemove),
      });
    }
  };

  const handleSaveProfile = async () => {
    if (!id || !profile) return;
    setSaving(true);
    setError(null);
    try {
      await api.updateProfile(id, profile);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };

  const handleStartInterview = async () => {
    if (!id || !profile) return;
    setStartingInterview(true);
    setError(null);
    try {
      // 1. Save latest edits first
      await api.updateProfile(id, profile);

      // 2. Create Interview Session & Generate Plan
      const sessionRes = await api.createInterview({
        profile_id: id,
        job_role: setupParams.job_role || 'Full Stack Engineer',
        job_description: setupParams.job_description || '',
        difficulty: setupParams.difficulty || 'mid',
        duration_minutes: setupParams.duration_minutes || 30,
        target_question_count: setupParams.target_question_count || 5,
      });

      // 3. Navigate to Interview Dashboard
      navigate(`/interviews/${sessionRes.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize interview plan.');
      setStartingInterview(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-600 font-medium text-sm">Structuring candidate profile and skills...</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <p className="text-red-600">Profile not found.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center space-x-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 mb-1.5">
            <Target className="w-3.5 h-3.5" />
            <span>Target Role: {jobRole}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Review Candidate Profile
          </h1>
          <p className="text-sm text-slate-600">
            Review the extracted skills and background below. You can adjust details before starting the practice questions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleSaveProfile}
            disabled={saving}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 bg-white text-slate-700 text-sm font-medium transition-colors"
          >
            <Save className="w-4 h-4 text-slate-500" />
            <span>{saving ? 'Saving...' : 'Save Draft'}</span>
          </button>

          <button
            type="button"
            onClick={handleStartInterview}
            disabled={startingInterview}
            className="flex items-center space-x-1.5 px-5 py-2 rounded-lg font-medium text-sm text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
          >
            {startingInterview ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Preparing Questions...</span>
              </>
            ) : (
              <>
                <span>Start Practice Session</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {saveSuccess && (
        <div className="mb-6 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-green-600" />
          <span>Profile changes saved successfully.</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT COLUMN: CANDIDATE INFO & SKILLS */}
        <div className="lg:col-span-2 space-y-6">
          {/* PERSONAL INFO & SUMMARY */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
              <User className="w-4 h-4 text-blue-600" />
              <span>Contact & Background</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => handleProfileFieldChange('full_name', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  value={profile.email || ''}
                  onChange={(e) => handleProfileFieldChange('email', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Estimated Experience</label>
                <div className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 text-sm font-medium">
                  {profile.years_of_experience} years
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Professional Summary</label>
              <textarea
                rows={3}
                value={profile.summary || ''}
                onChange={(e) => handleProfileFieldChange('summary', e.target.value)}
                placeholder="Brief summary of technical background..."
                className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* TECHNICAL SKILLS TAXONOMY */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                <Wrench className="w-4 h-4 text-blue-600" />
                <span>Extracted Skills</span>
              </h3>
              <span className="text-xs text-slate-500">
                {profile.technical_skills.length} skills identified
              </span>
            </div>

            {/* Add Skill Bar */}
            <div className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 border border-slate-200">
              <select
                value={skillCategory}
                onChange={(e) => setSkillCategory(e.target.value as any)}
                className="px-2.5 py-1.5 rounded-md bg-white text-xs text-slate-800 border border-slate-200 focus:outline-none"
              >
                <option value="languages">Language</option>
                <option value="frameworks">Framework</option>
                <option value="tools">Tool / Cloud</option>
              </select>

              <input
                type="text"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())}
                placeholder="Add missing skill (e.g. Docker, TypeScript)..."
                className="flex-1 px-2.5 py-1.5 bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
              />

              <button
                type="button"
                onClick={handleAddSkill}
                className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium flex items-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add</span>
              </button>
            </div>

            {/* Languages */}
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Programming Languages
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.programming_languages.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill('languages', skill)}
                      className="text-blue-500 hover:text-red-600 transition-colors"
                      title="Remove skill"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Frameworks */}
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Frameworks & Libraries
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.frameworks_libraries.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill('frameworks', skill)}
                      className="text-slate-500 hover:text-red-600 transition-colors"
                      title="Remove skill"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Tools */}
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Tools, Platforms & Databases
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.tools_platforms.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium bg-green-50 text-green-800 border border-green-200"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill('tools', skill)}
                      className="text-green-600 hover:text-red-600 transition-colors"
                      title="Remove skill"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* PROJECTS & EXPERIENCE */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
              <Briefcase className="w-4 h-4 text-blue-600" />
              <span>Projects & Work Experience</span>
            </h3>

            {/* Projects list */}
            {profile.projects.length > 0 && (
              <div className="space-y-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Projects ({profile.projects.length})
                </span>
                {profile.projects.map((proj, idx) => (
                  <div key={idx} className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="font-semibold text-sm text-slate-900">{proj.title}</div>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">{proj.description}</p>
                    {proj.technologies && proj.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {proj.technologies.map((t, tidx) => (
                          <span key={tidx} className="text-[11px] px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Experience list */}
            {profile.work_experience.length > 0 && (
              <div className="space-y-3 pt-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Experience ({profile.work_experience.length})
                </span>
                {profile.work_experience.map((exp, idx) => (
                  <div key={idx} className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-slate-900">{exp.role}</span>
                      <span className="text-xs text-slate-500">{exp.duration}</span>
                    </div>
                    <div className="text-xs text-blue-700 font-medium">{exp.company}</div>
                    {exp.responsibilities && exp.responsibilities.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs text-slate-600 list-disc list-inside">
                        {exp.responsibilities.slice(0, 3).map((r, ridx) => (
                          <li key={ridx}>{r}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: EVIDENCE MAPPING */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center space-x-2 text-sm font-semibold text-slate-900 mb-3">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>Resume Evidence</span>
            </div>

            <p className="text-xs text-slate-600 mb-4 leading-relaxed">
              Verified snippets extracted from your resume for <strong className="text-slate-800">{jobRole}</strong>.
            </p>

            <div className="space-y-3">
              {Object.keys(profile.evidence_map).length === 0 ? (
                <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>No direct evidence snippets extracted. Foundational questions will be prioritized.</span>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {Object.entries(profile.evidence_map).slice(0, 8).map(([skill, snippet], idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                      <div className="font-semibold text-blue-700 mb-0.5">{skill}</div>
                      <div className="text-slate-600 italic">"...{snippet}..."</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-5 pt-4 border-t border-slate-100 text-xs text-slate-600 space-y-2">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
                <span>Evidence confirmed in resume</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span>Partial keyword or secondary match</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                <span>Uncovered: Will be prioritized in questions</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
