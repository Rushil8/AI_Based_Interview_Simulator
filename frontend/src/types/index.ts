export interface SkillEvidence {
  skill: string;
  category: string;
  snippet?: string;
  confidence: number;
}

export interface ProjectItem {
  title: string;
  description: string;
  technologies: string[];
  role?: string;
  highlights: string[];
}

export interface EducationItem {
  degree: string;
  institution: string;
  year?: string;
  details?: string;
}

export interface ExperienceItem {
  role: string;
  company: string;
  duration?: string;
  responsibilities: string[];
}

export interface StructuredProfile {
  full_name: string;
  email?: string;
  phone?: string;
  summary?: string;
  technical_skills: string[];
  programming_languages: string[];
  frameworks_libraries: string[];
  tools_platforms: string[];
  projects: ProjectItem[];
  education: EducationItem[];
  work_experience: ExperienceItem[];
  achievements: string[];
  years_of_experience: number;
  evidence_map: Record<string, string>;
}

export interface CandidateProfileResponse {
  id: string;
  user_id?: string;
  resume_filename?: string;
  structured_profile: StructuredProfile;
  created_at: string;
  updated_at: string;
}

export interface CompetencyResponse {
  id: string;
  name: string;
  category: string;
  importance_weight: number;
  relevance_score: number;
  initial_strength: number;
  evidence?: string;
  coverage_status: 'covered' | 'partially_covered' | 'uncovered';
}

export interface InterviewSessionResponse {
  id: string;
  user_id?: string;
  profile_id?: string;
  job_role: string;
  job_description?: string;
  status: string;
  difficulty: string;
  duration_minutes: number;
  target_question_count: number;
  current_question_index: number;
  started_at: string;
  completed_at?: string;
  competencies: CompetencyResponse[];
  questions: QuestionPublicResponse[];
}

export interface QuestionPublicResponse {
  id: string;
  session_id: string;
  competency_id?: string;
  competency_name?: string;
  sequence_number: number;
  question_text: string;
  question_type: string;
  difficulty: string;
  maximum_score: number;
  is_adaptive_followup: boolean;
  adaptation_reason?: string;
}

export interface EvaluationDimensionBreakdown {
  score: number;
  weight: number;
  contribution: number;
  criteria?: string;
  evidence?: string;
}

export interface AnswerEvaluationResponse {
  id: string;
  answer_id: string;
  relevance_score: number;
  technical_score: number;
  completeness_score: number;
  communication_score: number;
  weighted_score: number;
  semantic_similarity: number;
  evidence: Record<string, string>;
  correct_concepts: string[];
  missing_concepts: string[];
  incorrect_claims: string[];
  suggested_improvements: string[];
  dimension_breakdown?: Record<string, EvaluationDimensionBreakdown>;
  confidence_score: number;
  rubric_version: string;
  evaluation_status: string;
  evaluated_at: string;
}

export interface InterviewProgressResponse {
  session_id: string;
  current_question_index: number;
  target_question_count: number;
  answered_count: number;
  remaining_count: number;
  provisional_score?: number | null;
  competency_coverage_pct: number;
  status: string;
  can_proceed: boolean;
}

export interface NextQuestionResponse {
  is_finished: boolean;
  question?: QuestionPublicResponse | null;
  adaptation_reason?: string;
  progress: InterviewProgressResponse;
}

export interface CompetencyPerformance {
  competency_id: string;
  name: string;
  category: string;
  score: number;
  importance_weight: number;
  coverage_status: string;
  questions_tested: number;
}

export interface DimensionScores {
  relevance: number;
  technical_correctness: number;
  completeness: number;
  communication: number;
}

export interface QuestionReviewItem {
  sequence_number: number;
  question_text: string;
  competency_name: string;
  difficulty: string;
  question_type: string;
  answer_text: string;
  weighted_score: number;
  relevance_score: number;
  technical_score: number;
  completeness_score: number;
  communication_score: number;
  semantic_similarity: number;
  correct_concepts: string[];
  missing_concepts: string[];
  suggested_improvements: string[];
}

export interface FeedbackReport {
  overall_strengths: string[];
  technical_strengths: string[];
  missing_concepts: string[];
  weak_competencies: string[];
  corrections_and_explanations: string[];
  communication_improvements: string[];
  practice_exercises: string[];
  recommended_topics_to_revise: string[];
  recommended_next_steps: string[];
}

export interface SessionReportResponse {
  id: string;
  session_id: string;
  job_role: string;
  overall_score: number;
  performance_summary: string;
  dimension_scores: DimensionScores;
  competency_scores: CompetencyPerformance[];
  strongest_competencies: string[];
  weakest_competencies: string[];
  answered_count: number;
  skipped_count: number;
  coverage_pct: number;
  difficulty_distribution: Record<string, number>;
  question_reviews: QuestionReviewItem[];
  feedback: FeedbackReport;
  hiring_disclaimer: string;
  generated_at: string;
}

export interface SessionHistoryItem {
  id: string;
  job_role: string;
  difficulty: string;
  status: string;
  target_question_count: number;
  started_at: string;
  completed_at?: string;
  overall_score?: number | null;
  has_report: boolean;
}

export interface SystemConfigResponse {
  app_name: string;
  app_version: string;
  environment: string;
  gemini_model: string;
  mock_ai: boolean;
  rubric_version: string;
  weights: {
    relevance: number;
    technical_correctness: number;
    completeness: number;
    communication: number;
  };
  semantic_flag_threshold: number;
}
