from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId


class TemplateVariables(BaseModel):
    """Template variables sub-document"""
    candidate_name: str = "{{candidate_name}}"
    position_title: str = "{{position_title}}"
    start_date: str = "{{start_date}}"
    base_salary: str = "{{base_salary}}"
    department: str = "{{department}}"
    manager_name: str = "{{manager_name}}"
    company_name: str = "{{company_name}}"
    
    # Additional custom variables
    custom_variables: Dict[str, str] = {}


class OfferTemplateModel(BaseModel):
    """Offer Template document model for MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: Optional[str] = None
    
    # Template content
    subject_template: str = "Job Offer - {{position_title}} at {{company_name}}"
    body_html: str
    body_text: Optional[str] = None  # Plain text version
    
    # Branding
    company_logo_url: Optional[str] = None
    theme_color: str = "#2563eb"  # Default blue
    font_family: str = "Arial, sans-serif"
    
    # Template variables
    available_variables: TemplateVariables = TemplateVariables()
    required_variables: List[str] = ["candidate_name", "position_title"]
    
    # Template metadata
    created_by: str  # User ID
    template_type: str = "offer_letter"  # "offer_letter", "interview_invitation", "rejection"
    category: Optional[str] = None  # "executive", "technical", "intern"
    
    # Usage statistics
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    is_default: bool = False
    
    # Version control
    version: str = "1.0"
    version_history: List[Dict[str, Any]] = []
    
    # Approval workflow (if needed)
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class GeneratedOfferModel(BaseModel):
    """Generated offer document model"""
    id: Optional[str] = Field(None, alias="_id")
    template_id: str
    resume_id: str
    
    # Generated content
    subject: str
    body_html: str
    body_text: Optional[str] = None
    
    # Variable values used
    variable_values: Dict[str, str] = {}
    
    # Recipient information
    candidate_email: str
    candidate_name: str
    
    # Generation metadata
    generated_by: str  # User ID
    generation_method: str = "template"  # "template", "ai_generated"
    
    # Status
    status: str = "draft"  # "draft", "sent", "viewed", "accepted", "declined", "expired"
    
    # Email tracking
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_type: Optional[str] = None  # "accepted", "declined", "negotiation"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
