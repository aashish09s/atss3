from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId


class ParsedJDData(BaseModel):
    """Parsed job description data sub-document"""
    title: Optional[str] = None
    department: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[Dict[str, Any]] = None
    
    # Requirements
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    required_experience: Optional[str] = None
    education_requirements: List[str] = []
    
    # Job details
    responsibilities: List[str] = []
    benefits: List[str] = []
    company_info: Optional[Dict[str, Any]] = None


class JobDescriptionModel(BaseModel):
    """Job Description document model for MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description_text: str
    
    # Upload information
    uploaded_by: str  # User ID
    source_type: str = "text"  # "text", "file"
    original_filename: Optional[str] = None
    
    # Parsed information
    parsed_jd: Optional[ParsedJDData] = None
    
    # AI processing metadata
    ai_provider_used: Optional[str] = None  # "gemini", "spacy"
    ai_confidence: Optional[float] = None
    processing_errors: List[str] = []
    
    # Job posting metadata
    job_code: Optional[str] = None
    department: Optional[str] = None
    hiring_manager: Optional[str] = None
    
    # Salary/Budget information
    salary_range: Optional[Dict[str, Any]] = None  # {"min": 50000, "max": 80000, "currency": "USD"}
    budget_amount: Optional[float] = None  # Total budget for the position
    
    # Status
    status: str = "active"  # "active", "closed", "on_hold", "cancelled"
    is_active: bool = True  # Active/Inactive toggle
    applications_count: int = 0
    
    # Invoice information
    invoice_date: Optional[datetime] = None  # Date when invoice was generated/sent
    
    # Requirement fulfillment status
    requirement_fulfilled: bool = False  # Whether the requirement is fulfilled or not
    
    # Matching statistics
    total_matches_run: int = 0
    average_match_score: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ATSScoreModel(BaseModel):
    """ATS Score document model"""
    id: Optional[str] = Field(None, alias="_id")
    resume_id: str
    jd_id: str
    
    # Scoring results
    overall_score: float  # 0-100
    skill_match_score: Optional[float] = None
    experience_match_score: Optional[float] = None
    education_match_score: Optional[float] = None
    
    # Detailed analysis
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    extra_skills: List[str] = []
    
    # Recommendations
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_suggestions: List[str] = []
    
    # AI processing metadata
    ai_provider: str
    scoring_algorithm: str = "combined"  # "gemini", "tfidf", "combined"
    confidence_level: Optional[float] = None
    
    # Timestamps
    scored_by: str  # User ID
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
