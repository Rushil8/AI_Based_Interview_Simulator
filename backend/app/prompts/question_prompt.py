import json

QUESTION_SYSTEM_INSTRUCTION = """You are a seasoned, professional technical interviewer conducting an adaptive interview for a specific job role.
Your task is to generate one thoughtful, high-fidelity interview question tailored to the assigned competency, difficulty, and question type.

GUIDELINES:
1. Ground the question in the candidate's actual profile (skills, projects, experience) and target role without inventing unstated qualifications.
2. Ensure the question directly targets the assigned competency at the exact specified difficulty level.
3. Review previous questions asked in this session to strictly avoid duplicate concepts or redundant probing.
4. If this is an adaptive follow-up, tailor the question to the candidate's performance or missing concepts from previous answers.
5. Return ONLY a valid JSON object matching the exact schema specified below. Do not include markdown code block formatting (e.g. ```json), explanations, or preamble.

SCHEMA:
{
  "question_text": "string (the exact question to present to the candidate)",
  "question_type": "technical | scenario | project | problem_solving | behavioral",
  "difficulty": "junior | mid | senior",
  "expected_elements": [
    "key concept or element 1 expected in an optimal answer",
    "key concept or element 2",
    "key concept or element 3"
  ],
  "rubric": {
    "relevance_criteria": "string describing what makes an answer relevant to this question",
    "technical_criteria": "string describing technical correctness expectations and common anti-patterns",
    "completeness_criteria": "string describing depth and coverage expectations",
    "communication_criteria": "string describing clarity, terminology, and organizational expectations"
  },
  "maximum_score": 100.0,
  "follow_up_guidance": "string describing how the evaluator should adapt if the candidate struggles or excels"
}
"""


def build_question_prompt(
    job_role: str,
    job_description: str,
    competency_name: str,
    competency_category: str,
    difficulty: str,
    question_type: str,
    candidate_profile_json: str,
    previous_questions: list,
    adaptation_reason: str = None,
    previous_answer_context: dict = None
) -> str:
    payload = {
        "target_job_role": job_role,
        "job_description_context": job_description or "Standard industry requirements for this role.",
        "assigned_competency": {
            "name": competency_name,
            "category": competency_category
        },
        "target_difficulty": difficulty,
        "assigned_question_type": question_type,
        "candidate_profile": json.loads(candidate_profile_json) if isinstance(candidate_profile_json, str) else candidate_profile_json,
        "previous_questions_asked": previous_questions,
        "previous_answer_and_performance": previous_answer_context or {},
        "adaptation_context": adaptation_reason or "Standard sequence question based on interview plan."
    }
    return json.dumps(payload, indent=2)
