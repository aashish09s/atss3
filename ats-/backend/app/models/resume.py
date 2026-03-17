from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId


class ParsedResumeData(BaseModel):
    """Parsed resume data sub-document"""
    name: Optional[str] = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    summary: Optional[str] = None
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []


class ResumeModel(BaseModel):
    """Resume document model for MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    filename: str
    file_url: str
    original_size: Optional[int] = None
    content_type: Optional[str] = None
    
    # Ownership and sharing
    uploaded_by: str  # User ID who uploaded
    shared_with_manager: bool = False
    shared_by: Optional[str] = None  # User ID who shared
    shared_at: Optional[datetime] = None
    
    # Processing status
    processing_status: str = "pending"  # "pending", "processing", "completed", "failed"
    
    # Parsed data (preview for listing)
    parsed_data: Optional[ParsedResumeData] = None
    
    # ATS scoring
    ats_score: Optional[float] = None
    ats_suggestions: Optional[List[str]] = []
    last_scored_against: Optional[str] = None  # JD ID
    
    # Resume status in hiring pipeline
    status: str = "submission"  # "submission", "shortlisting", "interview", "reject", "select", "offer_letter", "onboarding"
    status_updated_by: Optional[str] = None
    status_updated_at: Optional[datetime] = None
    status_history: List[Dict[str, Any]] = []
    
    # AI processing metadata
    ai_provider_used: Optional[str] = None  # "gemini", "spacy"
    ai_confidence: Optional[float] = None
    processing_errors: List[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ParsedResumeModel(BaseModel):
    """Detailed parsed resume document model"""
    id: Optional[str] = Field(None, alias="_id")
    resume_id: str  # Reference to ResumeModel
    
    # Extracted content
    raw_text: str
    cleaned_text: Optional[str] = None
    
    # Detailed parsed information
    candidate_name: Optional[str] = None
    contact_info: Dict[str, Any] = {}
    professional_summary: Optional[str] = None
    
    # Skills and technologies
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    certifications: List[Dict[str, Any]] = []
    languages: List[Dict[str, Any]] = []
    
    # Experience details
    work_experience: List[Dict[str, Any]] = []
    total_experience_years: Optional[float] = None
    
    # Education details
    education: List[Dict[str, Any]] = []
    highest_degree: Optional[str] = None
    
    # Additional information
    projects: List[Dict[str, Any]] = []
    achievements: List[str] = []
    publications: List[Dict[str, Any]] = []
    
    # AI processing metadata
    ai_provider: str  # "gemini", "spacy"
    ai_confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
