import pytest
from app.services.resume_service import resume_service, ResumeParsingError


def test_valid_pdf_extraction():
    with open("sample_data/sample_resume.pdf", "rb") as f:
        pdf_bytes = f.read()

    result = resume_service.extract_text_from_pdf_bytes(pdf_bytes, filename="sample_resume.pdf")
    assert result["page_count"] >= 1
    assert "Alex Morgan" in result["text"]
    assert "FastAPI" in result["text"]
    assert "React" in result["text"]
    assert result["char_count"] > 100


def test_empty_pdf_bytes_raises_error():
    with pytest.raises(ResumeParsingError):
        resume_service.extract_text_from_pdf_bytes(b"", filename="empty.pdf")


def test_corrupted_pdf_raises_error():
    with pytest.raises(ResumeParsingError):
        resume_service.extract_text_from_pdf_bytes(b"not a valid pdf content", filename="bad.pdf")
