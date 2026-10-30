import {
  CandidateProfileResponse,
  StructuredProfile,
  InterviewSessionResponse,
  QuestionPublicResponse,
  AnswerEvaluationResponse,
  NextQuestionResponse,
  InterviewProgressResponse,
  SessionReportResponse,
  SessionHistoryItem,
  SystemConfigResponse,
} from '../types';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || JSON.stringify(errorJson);
    } catch {
      errorDetail = res.statusText || `HTTP ${res.status}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Resume & Profile
  async uploadResume(file: File): Promise<CandidateProfileResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/resumes/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<CandidateProfileResponse>(res);
  },

  async getProfile(profileId: string): Promise<CandidateProfileResponse> {
    const res = await fetch(`${BASE_URL}/profiles/${profileId}`);
    return handleResponse<CandidateProfileResponse>(res);
  },

  async updateProfile(profileId: string, profile: StructuredProfile): Promise<CandidateProfileResponse> {
    const res = await fetch(`${BASE_URL}/profiles/${profileId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ structured_profile: profile }),
    });
    return handleResponse<CandidateProfileResponse>(res);
  },

  async deleteProfile(profileId: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/profiles/${profileId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete profile');
  },

  // Interviews
  async createInterview(payload: {
    profile_id: string;
    job_role: string;
    job_description?: string;
    difficulty: string;
    duration_minutes: number;
    target_question_count: number;
  }): Promise<InterviewSessionResponse> {
    const res = await fetch(`${BASE_URL}/interviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<InterviewSessionResponse>(res);
  },

  async getInterview(sessionId: string): Promise<InterviewSessionResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}`);
    return handleResponse<InterviewSessionResponse>(res);
  },

  async getCurrentQuestion(sessionId: string): Promise<QuestionPublicResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}/current-question`);
    return handleResponse<QuestionPublicResponse>(res);
  },

  async submitAnswer(sessionId: string, questionId: string, answerText: string): Promise<AnswerEvaluationResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}/answers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: questionId,
        answer_text: answerText,
      }),
    });
    return handleResponse<AnswerEvaluationResponse>(res);
  },

  async getAnswerEvaluation(answerId: string): Promise<AnswerEvaluationResponse> {
    const res = await fetch(`${BASE_URL}/answers/${answerId}/evaluation`);
    return handleResponse<AnswerEvaluationResponse>(res);
  },

  async advanceNextQuestion(sessionId: string): Promise<NextQuestionResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}/next-question`, {
      method: 'POST',
    });
    return handleResponse<NextQuestionResponse>(res);
  },

  async getInterviewProgress(sessionId: string): Promise<InterviewProgressResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}/progress`);
    return handleResponse<InterviewProgressResponse>(res);
  },

  async completeInterview(sessionId: string): Promise<SessionReportResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}/complete`, {
      method: 'POST',
    });
    return handleResponse<SessionReportResponse>(res);
  },

  async getSessionReport(sessionId: string): Promise<SessionReportResponse> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}/report`);
    return handleResponse<SessionReportResponse>(res);
  },

  async deleteInterview(sessionId: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/interviews/${sessionId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete interview');
  },

  // History & Config
  async getUserInterviews(limit = 20, offset = 0): Promise<SessionHistoryItem[]> {
    const res = await fetch(`${BASE_URL}/users/me/interviews?limit=${limit}&offset=${offset}`);
    return handleResponse<SessionHistoryItem[]>(res);
  },

  async getSystemConfig(): Promise<SystemConfigResponse> {
    const res = await fetch(`${BASE_URL}/config`);
    return handleResponse<SystemConfigResponse>(res);
  },
};
