import io
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200


def test_favicon_endpoint(client: TestClient):
    response = client.get("/favicon.ico")
    assert response.status_code in [200, 204]


def test_system_config_endpoint(client: TestClient):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["weights"]["technical_correctness"] == 0.40
    assert data["weights"]["relevance"] == 0.20


def test_full_interview_workflow(client: TestClient):
    # 1. Upload sample resume PDF
    with open("sample_data/sample_resume.pdf", "rb") as f:
        pdf_bytes = f.read()

    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("sample_resume.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201
    profile_data = upload_res.json()
    profile_id = profile_data["id"]
    assert profile_data["structured_profile"]["full_name"] == "Alex Morgan"

    # 2. Candidate Reviews and Updates Profile
    patch_res = client.patch(
        f"/api/profiles/{profile_id}",
        json={"structured_profile": profile_data["structured_profile"]}
    )
    assert patch_res.status_code == 200

    # 3. Create Interview Session
    session_res = client.post(
        "/api/interviews",
        json={
            "profile_id": profile_id,
            "job_role": "Full Stack Engineer",
            "job_description": "Building high-performance web systems with React and FastAPI.",
            "difficulty": "mid",
            "duration_minutes": 30,
            "target_question_count": 3
        }
    )
    assert session_res.status_code == 201
    session_data = session_res.json()
    session_id = session_data["id"]
    assert len(session_data["competencies"]) >= 3
    assert len(session_data["questions"]) == 1

    # 4. Fetch Current Question (Verifying rubric is hidden)
    current_q_res = client.get(f"/api/interviews/{session_id}/current-question")
    assert current_q_res.status_code == 200
    q_data = current_q_res.json()
    q_id = q_data["id"]
    assert "rubric" not in q_data  # Public view hides rubric!
    assert "expected_elements" not in q_data
    assert len(q_data["question_text"]) > 10

    # 5. Submit Answer & Receive 4-dimension Evaluation
    answer_text = (
        "In React, state represents dynamic local data while props are read-only inputs passed by the parent. "
        "To optimize rendering of large lists, I utilize virtual windowing techniques like react-window to only mount "
        "visible DOM nodes. Furthermore, memoization with useMemo and useCallback helps prevent unnecessary child updates."
    )
    ans_res = client.post(
        f"/api/interviews/{session_id}/answers",
        json={"question_id": q_id, "answer_text": answer_text}
    )
    assert ans_res.status_code == 201
    eval_data = ans_res.json()
    assert eval_data["relevance_score"] > 0
    assert eval_data["technical_score"] > 0
    assert eval_data["completeness_score"] > 0
    assert eval_data["communication_score"] > 0
    assert eval_data["weighted_score"] > 0
    assert "relevance" in eval_data["dimension_breakdown"]

    # 6. Check Progress
    progress_res = client.get(f"/api/interviews/{session_id}/progress")
    assert progress_res.status_code == 200
    prog_data = progress_res.json()
    assert prog_data["answered_count"] == 1
    assert prog_data["can_proceed"] is True

    # 7. Advance to Next Question (Adaptive Progression)
    next_res = client.post(f"/api/interviews/{session_id}/next-question")
    assert next_res.status_code == 200
    next_data = next_res.json()
    assert next_data["is_finished"] is False
    assert next_data["question"] is not None
    next_q_id = next_data["question"]["id"]
    assert next_q_id != q_id  # New question generated

    # 8. Complete Interview and Fetch Persisted Final Report
    complete_res = client.post(f"/api/interviews/{session_id}/complete")
    assert complete_res.status_code == 200
    report_data = complete_res.json()
    assert report_data["overall_score"] > 0
    assert "dimension_scores" in report_data
    assert "feedback" in report_data
    assert "hiring_disclaimer" in report_data

    # 9. Verify Session History List
    history_res = client.get("/api/users/me/interviews")
    assert history_res.status_code == 200
    history_list = history_res.json()
    assert len(history_list) >= 1
    assert any(h["id"] == session_id for h in history_list)
