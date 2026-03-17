from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from bson import ObjectId
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/hr/parsed", tags=["Parsed Profiles"])


class ParsedProfileResponse(BaseModel):
    id: str
    resume_id: str
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience: List[Dict[Any, Any]] = []
    education: List[Dict[Any, Any]] = []
    summary: Optional[str] = ""
    location: Optional[str] = None
    certifications: List[str] = []
    projects: List[Dict[Any, Any]] = []  # Changed from List[str] to List[Dict[Any, Any]]
    created_at: datetime


@router.get("/", response_model=List[ParsedProfileResponse])
async def get_parsed_profiles(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get all parsed candidate profiles"""
    db = await get_db()
    
    # Get all resumes - Admins can see all resumes, HR users see only their own
    resume_query: Dict[str, Any] = {}
    if current_user["role"] != "admin":
        resume_query["uploaded_by"] = str(current_user["_id"])
    resumes = await db.resumes.find(resume_query).to_list(None)
    
    resume_ids = [str(resume["_id"]) for resume in resumes]
    
    # Get parsed profiles for these resumes
    profiles = await db.parsed_resumes.find({
        "resume_id": {"$in": resume_ids}
    }).sort("created_at", -1).to_list(None)
    
    result = []
    for profile in profiles:
        try:
            # Normalize education field - handle string values
            education = profile.get("education", [])
            if isinstance(education, str):
                education = [{"institution": education}]
            elif isinstance(education, list):
                normalized_education = []
                for edu in education:
                    if isinstance(edu, str):
                        normalized_education.append({"institution": edu})
                    elif isinstance(edu, dict):
                        normalized_education.append(edu)
                education = normalized_education
            
            # Normalize experience field - handle string values
            experience = profile.get("experience", [])
            if isinstance(experience, str):
                experience = [{"description": experience}]
            elif isinstance(experience, list):
                normalized_experience = []
                for exp in experience:
                    if isinstance(exp, str):
                        normalized_experience.append({"description": exp})
                    elif isinstance(exp, dict):
                        normalized_experience.append(exp)
                experience = normalized_experience
            
            # Normalize projects field - handle both string and dict formats
            projects = profile.get("projects", [])
            if isinstance(projects, str):
                projects = [{"name": projects}]
            elif isinstance(projects, list):
                normalized_projects = []
                for proj in projects:
                    if isinstance(proj, str):
                        normalized_projects.append({"name": proj})
                    elif isinstance(proj, dict):
                        normalized_projects.append(proj)
                projects = normalized_projects
            
            # Normalize summary field - ensure it's always a string
            summary = profile.get("summary", "")
            if summary is None:
                summary = ""
            elif not isinstance(summary, str):
                summary = str(summary)
            
            # Normalize skills field - ensure it's always a list of strings
            skills = profile.get("skills", [])
            if isinstance(skills, str):
                skills = [skills]
            elif isinstance(skills, list):
                skills = [str(skill) for skill in skills if skill is not None]
            else:
                skills = []
            
            # Normalize certifications field - ensure it's always a list of strings
            certifications = profile.get("certifications", [])
            if isinstance(certifications, str):
                certifications = [certifications]
            elif isinstance(certifications, list):
                certifications = [str(cert) for cert in certifications if cert is not None]
            else:
                certifications = []
            
            result.append(ParsedProfileResponse(
                id=str(profile["_id"]),
                resume_id=profile["resume_id"],
                candidate_name=profile.get("candidate_name", "Unknown"),
                email=profile.get("email"),
                phone=profile.get("phone"),
                skills=skills,  # Use normalized skills
                experience=experience,
                education=education,
                summary=summary,  # Use normalized summary
                location=profile.get("location"),
                certifications=certifications,  # Use normalized certifications
                projects=projects,  # Use normalized projects
                created_at=profile["created_at"]
            ))
        except Exception as e:
            print(f"Error processing profile {profile.get('_id')}: {e}")
            print(f"Profile data: {profile}")
            import traceback
            traceback.print_exc()
            continue
    
    return result


@router.get("/{profile_id}", response_model=ParsedProfileResponse)
async def get_parsed_profile(
    profile_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get specific parsed profile"""
    db = await get_db()
    
    try:
        profile_object_id = ObjectId(profile_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid profile ID"
        )
    
    profile = await db.parsed_resumes.find_one({"_id": profile_object_id})
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Verify ownership through resume - Admins can see any resume, HR users see only their own
    resume_query: Dict[str, Any] = {"_id": ObjectId(profile["resume_id"])}
    if current_user["role"] != "admin":
        resume_query["uploaded_by"] = str(current_user["_id"])
    resume = await db.resumes.find_one(resume_query)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ParsedProfileResponse(
        id=str(profile["_id"]),
        resume_id=profile["resume_id"],
        candidate_name=profile.get("candidate_name", "Unknown"),
        email=profile.get("email"),
        phone=profile.get("phone"),
        skills=profile.get("skills", []),
        experience=profile.get("experience", []),
        education=profile.get("education", []),
        summary=profile.get("summary", ""),
        location=profile.get("location"),
        certifications=profile.get("certifications", []),
        projects=profile.get("projects", []),
        created_at=profile["created_at"]
    )
