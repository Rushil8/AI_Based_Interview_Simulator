import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import CandidateProfile
from app.schemas.profile import CandidateProfileResponse, CandidateProfileUpdate, StructuredProfile

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/{profile_id}", response_model=CandidateProfileResponse)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")

    structured_dict = json.loads(profile.structured_profile_json)
    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        resume_filename=profile.resume_filename,
        structured_profile=StructuredProfile(**structured_dict),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch("/{profile_id}", response_model=CandidateProfileResponse)
def update_profile(
    profile_id: str,
    update_data: CandidateProfileUpdate,
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")

    profile.structured_profile_json = json.dumps(update_data.structured_profile.model_dump())
    db.commit()
    db.refresh(profile)

    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        resume_filename=profile.resume_filename,
        structured_profile=update_data.structured_profile,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")

    db.delete(profile)
    db.commit()
    return None
