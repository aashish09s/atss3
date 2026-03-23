from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class AssessmentQuestion(BaseModel):
    id: str
    question: str
    question_type: str  # "text", "mcq", "rating"
    options: Optional[List[str]] = None  # for MCQ


class AssessmentModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    resume_id: str
    jd_id: str
    candidate_name: str
    candidate_email: str
    jd_title: str
    token: str  # unique access token
    token_hash: str  # hashed token stored in DB
    status: str = "pending"  # "pending", "completed", "expired"
    
    # Who sent and when
    sent_by: str  # HR user id
    sent_by_name: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Candidate response
    completed_at: Optional[datetime] = None
    candidate_responses: Optional[Dict[str, Any]] = None
    
    # Extra info
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
