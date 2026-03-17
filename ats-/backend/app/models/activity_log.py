from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class ActivityLogModel(BaseModel):
    """Activity log document model for audit trail"""
    id: Optional[str] = Field(None, alias="_id")
    
    # Who performed the action
    user_id: str
    user_role: str
    user_email: Optional[str] = None
    
    # What action was performed
    action: str  # "create", "update", "delete", "share", "status_change", "login", "logout"
    entity_type: str  # "resume", "user", "jd", "template", "inbox"
    entity_id: Optional[str] = None
    
    # Action details
    description: str
    changes: Optional[Dict[str, Any]] = None  # Before/after values for updates
    metadata: Optional[Dict[str, Any]] = None  # Additional context
    
    # Request information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # System information
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response_status: Optional[int] = None
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class SystemMetricsModel(BaseModel):
    """System metrics document model"""
    id: Optional[str] = Field(None, alias="_id")
    
    # API usage metrics
    total_api_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_response_time_ms: Optional[float] = None
    
    # Feature usage
    resume_uploads: int = 0
    ai_parsing_requests: int = 0
    ats_scoring_requests: int = 0
    email_scans: int = 0
    
    # User activity
    active_users_today: int = 0
    new_users_today: int = 0
    total_sessions: int = 0
    
    # System resources
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    disk_usage_gb: Optional[float] = None
    
    # Database stats
    total_documents: Optional[int] = None
    database_size_mb: Optional[float] = None
    
    # Collection date
    date: datetime = Field(default_factory=lambda: datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
