from app.services.profile_service import profile_service


def test_profile_extraction_full():
    sample_text = """
    Jane Doe
    jane.doe@techcorp.com | (555) 987-6543
    
    Summary
    Full Stack Developer specializing in React, TypeScript, and FastAPI backends.
    
    Technical Skills
    Languages: Python, TypeScript, SQL, Bash
    Frameworks: React, FastAPI, Node.js, Next.js
    Tools: Docker, Git, PostgreSQL
    
    Work Experience
    Senior Software Engineer at DevCorp | 2021 - Present
    - Developed high throughput microservices using FastAPI and PostgreSQL.
    - Improved page rendering performance using React memoization.
    
    Projects
    Real-Time Analytics Dashboard
    Built live metrics visualizer with TypeScript, React, and WebSockets.
    
    Education
    B.S. in Computer Science, University of Technology, 2020
    """

    profile = profile_service.parse_profile_from_text(sample_text)
    assert profile.full_name == "Jane Doe"
    assert profile.email == "jane.doe@techcorp.com"
    assert "Python" in profile.programming_languages or "Python" in profile.technical_skills
    assert "React" in profile.frameworks_libraries or "React" in profile.technical_skills
    assert profile.years_of_experience >= 3.0
    assert len(profile.projects) >= 1
    assert len(profile.work_experience) >= 1
    assert "FastAPI" in profile.evidence_map or "React" in profile.evidence_map


def test_profile_extraction_missing_sections():
    sparse_text = """
    Bob Smith
    bob@example.com
    Just some general notes about coding in Python and React.
    """
    profile = profile_service.parse_profile_from_text(sparse_text)
    assert profile.email == "bob@example.com"
    assert "Python" in profile.technical_skills or "Python" in profile.programming_languages
    assert profile.education == []
    assert profile.work_experience == []
