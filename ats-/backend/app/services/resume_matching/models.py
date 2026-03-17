"""
Data models for the Resume Matching System.
Defines Pydantic models for structured data handling.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class FileType(str, Enum):
    """Supported file types for resume processing."""
    PDF = "pdf"
    DOCX = "docx"


class ProcessingStatus(str, Enum):
    """Status of resume processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeData(BaseModel):
    """Structured resume data extracted from documents."""
    id: Optional[str] = None
    file_name: str
    file_type: FileType
    
    # Extracted fields
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    years_of_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    
    # Metadata
    raw_text: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    
    # Embeddings
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None


class JobDescription(BaseModel):
    """Job description data model."""
    id: Optional[str] = None
    title: str
    company: Optional[str] = None
    description: str
    
    # Extracted requirements
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    
    # Embeddings
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MatchResult(BaseModel):
    """Result of resume-JD matching."""
    resume_id: str
    jd_id: str
    similarity_score: float
    
    # Filtering results
    skills_match: Dict[str, bool] = Field(default_factory=dict)
    experience_match: bool = True
    
    # GPT analysis (if available)
    gpt_analysis: Optional['GPTAnalysis'] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GPTAnalysis(BaseModel):
    """GPT-generated analysis for resume-JD matching."""
    match_percentage: float = Field(ge=0, le=100)
    missing_skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    # New structured outputs for hybrid local analysis
    match_score: Optional[float] = Field(default=None, ge=0, le=100)
    skill_match_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    weaknesses: List[str] = Field(default_factory=list)
    experience_relevance: Optional[str] = None
    experience_in_years: Optional[float] = None
    improvement_suggestions: List[str] = Field(default_factory=list)
    overall_assessment: str
    
    # Enhanced analysis fields
    technical_fit: Optional[str] = None
    experience_fit: Optional[str] = None
    recommendation: Optional[str] = None
    interview_questions: List[str] = Field(default_factory=list)
    
    # Metadata
    ai_model_used: str  # Changed from model_used to avoid conflict
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    
    class Config:
        protected_namespaces = ()  # Disable protected namespace warnings


class BulkProcessingJob(BaseModel):
    """Bulk processing job tracking."""
    job_id: str
    total_files: int
    processed_files: int = 0
    failed_files: int = 0
    
    status: ProcessingStatus = ProcessingStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class SearchQuery(BaseModel):
    """Search query for finding matching resumes."""
    jd_id: str
    top_k: int = Field(default=500, ge=1, le=10000)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Filtering criteria
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    required_skills: List[str] = Field(default_factory=list)
    
    # GPT analysis settings
    enable_gpt_analysis: bool = True
    max_gpt_resumes: int = Field(default=100, ge=1, le=1000)


class SearchResults(BaseModel):
    """Search results containing matched resumes."""
    query: SearchQuery
    total_matches: int
    results: List[MatchResult]
    
    # Processing metadata
    search_time_ms: float
    gpt_analysis_time_ms: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
