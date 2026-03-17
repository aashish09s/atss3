from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from bson import ObjectId


class ResumeShareModel(BaseModel):
    """Resume share document model for tracking resume sharing with clients"""
    id: Optional[str] = Field(None, alias="_id")
    
    # Resume and Client information
    resume_id: str
    client_email: str
    client_name: Optional[str] = None
    
    # Sharing details
    shared_by: str  # User ID who shared
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status tracking
    status: str = "shared"  # "shared", "viewed", "shortlisted", "interview", "offer", "rejected"
    status_updated_at: Optional[datetime] = None
    status_updated_by: Optional[str] = None
    
    # Email details
    email_subject: Optional[str] = None
    email_sent: bool = True
    attachment_included: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }




