from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ResumeOut(BaseModel):
    id: str
    filename: str
    file_url: str
    download_url: str
    uploaded_by: str
    status: str
    parsed_data: Optional[Dict[Any, Any]] = None
    ats_score: Optional[float] = None
    shared_with_manager: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True
