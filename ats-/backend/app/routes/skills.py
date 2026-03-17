"""
Skills API endpoints for managing comprehensive skills, job profiles, and certifications.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.services.skills_service import skills_service
from app.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skills", tags=["skills"])


# Pydantic models for request/response
class SkillSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


class SkillMatchRequest(BaseModel):
    resume_skills: List[str]
    jd_skills: List[str]


class TextExtractionRequest(BaseModel):
    text: str


class JobProfileSuggestionRequest(BaseModel):
    skills: List[str]
    limit: Optional[int] = 5


class CertificationSuggestionRequest(BaseModel):
    skills: List[str]
    limit: Optional[int] = 5


@router.get("/categories")
async def get_skill_categories(current_user: dict = Depends(get_current_user)):
    """Get all available skill categories."""
    try:
        categories = skills_service.get_skill_categories()
        return {
            "success": True,
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"Error getting skill categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get skill categories")


@router.get("/categories/{category}")
async def get_skills_by_category(
    category: str,
    current_user: dict = Depends(get_current_user)
):
    """Get skills for a specific category."""
    try:
        skills = skills_service.get_skills_by_category(category)
        if not skills:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return {
            "success": True,
            "category": category,
            "skills": skills,
            "total": len(skills)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skills for category {category}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get skills for category")


@router.post("/search")
async def search_skills(
    request: SkillSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search for skills that match the given query."""
    try:
        results = skills_service.search_skills(request.query, request.limit)
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching skills: {e}")
        raise HTTPException(status_code=500, detail="Failed to search skills")


@router.post("/extract")
async def extract_skills_from_text(
    request: TextExtractionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Extract skills from text and categorize them."""
    try:
        extracted_skills = skills_service.extract_skills_from_text(request.text)
        total_skills = sum(len(skills) for skills in extracted_skills.values())
        
        return {
            "success": True,
            "extracted_skills": extracted_skills,
            "total_skills": total_skills,
            "categories_found": len(extracted_skills)
        }
    except Exception as e:
        logger.error(f"Error extracting skills from text: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract skills from text")


@router.post("/match")
async def calculate_skill_match(
    request: SkillMatchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate skill match score between resume and job description."""
    try:
        match_result = skills_service.get_skill_match_score(
            request.resume_skills, 
            request.jd_skills
        )
        
        return {
            "success": True,
            "match_result": match_result
        }
    except Exception as e:
        logger.error(f"Error calculating skill match: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate skill match")


@router.get("/job-profiles")
async def get_job_profiles(current_user: dict = Depends(get_current_user)):
    """Get all available job profiles."""
    try:
        profiles = skills_service.job_profiles
        total_profiles = sum(len(profiles_list) for profiles_list in profiles.values())
        
        return {
            "success": True,
            "job_profiles": profiles,
            "total_categories": len(profiles),
            "total_profiles": total_profiles
        }
    except Exception as e:
        logger.error(f"Error getting job profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job profiles")


@router.post("/job-profiles/suggest")
async def suggest_job_profiles(
    request: JobProfileSuggestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Suggest job profiles based on skills."""
    try:
        suggestions = skills_service.suggest_job_profiles(request.skills, request.limit)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error suggesting job profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest job profiles")


@router.get("/certifications")
async def get_certifications(current_user: dict = Depends(get_current_user)):
    """Get all available certifications."""
    try:
        certifications = skills_service.certifications
        total_certifications = sum(len(certs) for certs in certifications.values())
        
        return {
            "success": True,
            "certifications": certifications,
            "total_categories": len(certifications),
            "total_certifications": total_certifications
        }
    except Exception as e:
        logger.error(f"Error getting certifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to get certifications")


@router.get("/certifications/categories")
async def get_certification_categories(current_user: dict = Depends(get_current_user)):
    """Get all available certification categories."""
    try:
        categories = skills_service.get_certification_categories()
        return {
            "success": True,
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"Error getting certification categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get certification categories")


@router.get("/certifications/categories/{category}")
async def get_certifications_by_category(
    category: str,
    current_user: dict = Depends(get_current_user)
):
    """Get certifications for a specific category."""
    try:
        certifications = skills_service.get_certifications_by_category(category)
        if not certifications:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return {
            "success": True,
            "category": category,
            "certifications": certifications,
            "total": len(certifications)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting certifications for category {category}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get certifications for category")


@router.post("/certifications/suggest")
async def suggest_certifications(
    request: CertificationSuggestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Suggest certifications based on skills."""
    try:
        suggestions = skills_service.suggest_certifications(request.skills, request.limit)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "total": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error suggesting certifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest certifications")


@router.get("/statistics")
async def get_skills_statistics(current_user: dict = Depends(get_current_user)):
    """Get statistics about the skills database."""
    try:
        stats = skills_service.get_skill_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting skills statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get skills statistics")


@router.get("/normalize/{skill}")
async def normalize_skill(
    skill: str,
    current_user: dict = Depends(get_current_user)
):
    """Normalize a skill name using the skills database."""
    try:
        normalized = skills_service.normalize_skill(skill)
        return {
            "success": True,
            "original_skill": skill,
            "normalized_skill": normalized,
            "found": normalized is not None
        }
    except Exception as e:
        logger.error(f"Error normalizing skill {skill}: {e}")
        raise HTTPException(status_code=500, detail="Failed to normalize skill")


@router.get("/related/{skill}")
async def get_related_skills(
    skill: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """Get skills related to the given skill."""
    try:
        related = skills_service.get_related_skills(skill, limit)
        return {
            "success": True,
            "skill": skill,
            "related_skills": related,
            "total": len(related)
        }
    except Exception as e:
        logger.error(f"Error getting related skills for {skill}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get related skills")
