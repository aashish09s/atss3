from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class IMAPSettings(BaseModel):
    """IMAP configuration sub-document"""
    host: str
    port: int = 993
    use_ssl: bool = True
    username: str
    password_encrypted: str  # Encrypted using Fernet
    
    # Folder settings
    inbox_folder: str = "INBOX"
    processed_folder: Optional[str] = None
    
    # Filter settings
    sender_whitelist: List[str] = []
    subject_keywords: List[str] = []


class ScanStatistics(BaseModel):
    """Scan statistics sub-document"""
    total_scans: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    total_emails_processed: int = 0
    total_attachments_found: int = 0
    total_resumes_extracted: int = 0
    
    # Last scan info
    last_scan_duration_ms: Optional[int] = None
    last_scan_errors: List[str] = []


class EmailInboxModel(BaseModel):
    """Email Inbox document model for MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str  # HR user who linked this inbox
    
    # Inbox identification
    inbox_name: str
    provider: str  # "gmail", "outlook", "imap", "exchange"
    email_address: EmailStr
    
    # IMAP/OAuth settings
    imap_settings: Optional[IMAPSettings] = None
    oauth_token: Optional[str] = None  # Encrypted OAuth token
    oauth_refresh_token: Optional[str] = None  # Encrypted refresh token
    oauth_expires_at: Optional[datetime] = None
    
    # Scanning configuration
    scan_schedule: str = "daily"  # "disabled", "hourly", "daily", "weekly", "monthly"
    scan_enabled: bool = True
    auto_process_attachments: bool = True
    
    # File filtering
    allowed_extensions: List[str] = [".pdf", ".doc", ".docx"]
    max_file_size_mb: int = 10
    
    # Processing statistics
    statistics: ScanStatistics = ScanStatistics()
    
    # Status
    status: str = "active"  # "active", "disabled", "error", "unauthorized"
    last_error: Optional[str] = None
    
    # Timestamps
    last_scanned_at: Optional[datetime] = None
    next_scan_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class EmailScanLogModel(BaseModel):
    """Email scan log document model"""
    id: Optional[str] = Field(None, alias="_id")
    inbox_id: str
    
    # Scan details
    scan_type: str = "scheduled"  # "scheduled", "manual", "realtime"
    scan_status: str = "running"  # "running", "completed", "failed", "cancelled"
    
    # Results
    emails_processed: int = 0
    attachments_found: int = 0
    resumes_extracted: int = 0
    processing_errors: List[Dict[str, Any]] = []
    
    # Performance
    scan_duration_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
