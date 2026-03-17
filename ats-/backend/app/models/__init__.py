# Models package for database document structures

# User models
from .user import UserModel, UserProfile, AccountRequestModel

# Resume models
from .resume import ResumeModel, ParsedResumeModel, ParsedResumeData

# Job Description models
from .job_description import JobDescriptionModel, ParsedJDData, ATSScoreModel

# Email models
from .email_inbox import EmailInboxModel, IMAPSettings, ScanStatistics, EmailScanLogModel

# Template models
from .offer_template import OfferTemplateModel, TemplateVariables, GeneratedOfferModel

# System models
from .activity_log import ActivityLogModel, SystemMetricsModel
from .websocket import WebSocketConnectionModel, WebSocketMessageModel

__all__ = [
    # User models
    "UserModel",
    "UserProfile", 
    "AccountRequestModel",
    
    # Resume models
    "ResumeModel",
    "ParsedResumeModel",
    "ParsedResumeData",
    
    # Job Description models
    "JobDescriptionModel",
    "ParsedJDData",
    "ATSScoreModel",
    
    # Email models
    "EmailInboxModel",
    "IMAPSettings",
    "ScanStatistics",
    "EmailScanLogModel",
    
    # Template models
    "OfferTemplateModel",
    "TemplateVariables",
    "GeneratedOfferModel",
    
    # System models
    "ActivityLogModel",
    "SystemMetricsModel",
    "WebSocketConnectionModel",
    "WebSocketMessageModel",
]
