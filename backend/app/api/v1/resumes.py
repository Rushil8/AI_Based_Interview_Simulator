import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.profile import CandidateProfile
from app.schemas.profile import CandidateProfileResponse, StructuredProfile
from app.services.resume_service import resume_service, ResumeParsingError
from app.services.profile_service import profile_service

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a candidate resume PDF.
    Validates file extension and size, extracts text using PyMuPDF,
    structures the candidate profile, and saves to database.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF documents (.pdf) are supported."
        )

    file_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    try:
        extraction = resume_service.extract_text_from_pdf_bytes(file_bytes, filename=file.filename)
    except ResumeParsingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while reading the PDF: {str(e)}"
        )

    # Parse structured profile
    structured = profile_service.parse_profile_from_text(extraction["text"])

    # Persist in DB
    profile_record = CandidateProfile(
        resume_filename=file.filename,
        resume_text=extraction["text"],
        structured_profile_json=json.dumps(structured.model_dump()),
    )
    db.add(profile_record)
    db.commit()
    db.refresh(profile_record)

    return CandidateProfileResponse(
        id=profile_record.id,
        user_id=profile_record.user_id,
        resume_filename=profile_record.resume_filename,
        structured_profile=structured,
        created_at=profile_record.created_at,
        updated_at=profile_record.updated_at,
    )
