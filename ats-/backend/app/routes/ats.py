from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.services.ai_service import score_resume_against_jd
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/hr/ats", tags=["ATS Scoring"])


class ATSScoreRequest(BaseModel):
    resume_id: str
    jd_id: str


class ATSScoreResponse(BaseModel):
    resume_id: str
    jd_id: str
    score: float
    reasons: List[str]
    missing_skills: List[str]
    strengths: List[str]
    scored_at: datetime


@router.post("/score", response_model=ATSScoreResponse)
async def calculate_ats_score(
    score_request: ATSScoreRequest,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Calculate ATS score for resume against JD"""
    db = await get_db()
    
    try:
        resume_object_id = ObjectId(score_request.resume_id)
        jd_object_id = ObjectId(score_request.jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume or JD ID"
        )
    
    # Get resume
    resume = await db.resumes.find_one({
        "_id": resume_object_id,
        "uploaded_by": str(current_user["_id"])
    })
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Get JD
    jd = await db.jds.find_one({
        "_id": jd_object_id,
        "uploaded_by": str(current_user["_id"])
    })
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    # Get parsed resume data
    parsed_resume = await db.parsed_resumes.find_one({
        "resume_id": score_request.resume_id
    })
    
    if not parsed_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parsed resume data not found"
        )
    
    try:
        # Calculate score
        score_result = await score_resume_against_jd(
            parsed_resume.get("raw_text", ""),
            jd["description_text"],
            parsed_resume,
            jd.get("parsed_jd")
        )
        
        # Update resume with ATS score
        await db.resumes.update_one(
            {"_id": resume_object_id},
            {
                "$set": {
                    "ats_score": score_result.get("score", 0.0),
                    "ats_details": score_result,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return ATSScoreResponse(
            resume_id=score_request.resume_id,
            jd_id=score_request.jd_id,
            score=score_result.get("score", 0.0),
            reasons=score_result.get("reasons", []),
            missing_skills=score_result.get("missing_skills", []),
            strengths=score_result.get("strengths", []),
            scored_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate ATS score: {str(e)}"
        )
