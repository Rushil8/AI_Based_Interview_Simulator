from app.services.competency_service import competency_service
from app.services.profile_service import profile_service


def test_competency_mapping_and_similarity():
    sample_text = """
    Alice Johnson
    alice@example.com
    
    Technical Skills
    Python, FastAPI, PostgreSQL, Docker, AWS, React, TypeScript
    
    Work Experience
    Backend Engineer at ScaleCo | 2021 - 2024
    - Built REST APIs and optimized relational database queries in PostgreSQL.
    """
    profile = profile_service.parse_profile_from_text(sample_text)

    competencies = competency_service.generate_and_map_competencies(
        job_role="Backend Developer",
        job_description="Looking for an engineer to build FastAPI backends and PostgreSQL databases.",
        profile=profile
    )

    assert len(competencies) >= 3
    comp_names = [c["name"] for c in competencies]
    assert any("Database" in name or "Server" in name or "Backend" in name for name in comp_names)

    # Check that competencies have evidence and coverage status
    for c in competencies:
        assert c["coverage_status"] in ["covered", "partially_covered", "uncovered"]
        assert 0.0 <= c["initial_strength"] <= 1.0
        assert c["importance_weight"] > 0.0


def test_cosine_similarity_calculation():
    text_a = "Building scalable REST APIs with FastAPI and PostgreSQL database indexing."
    text_b = "Backend API development using Python and relational databases."
    text_c = "Watercolor painting of European landscapes in springtime."

    sim_related = competency_service.compute_similarity(text_a, text_b)
    sim_unrelated = competency_service.compute_similarity(text_a, text_c)

    assert sim_related > sim_unrelated
    assert sim_related > 0.10
    assert sim_unrelated < 0.08
