from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class OnboardingStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    expired = "expired"

class OnboardingInvitationCreate(BaseModel):
    candidate_email: EmailStr
    candidate_name: str
    position: str
    company_name: str

class PersonalDetails(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    date_of_birth: str
    address: str
    city: str
    state: str
    pincode: str

class OnboardingSubmission(BaseModel):
    personal_details: PersonalDetails
    # Documents will be handled as files in the request

class OnboardingInvitationResponse(BaseModel):
    id: str
    candidate_email: str
    candidate_name: str
    position: str
    company_name: str
    status: OnboardingStatus
    sent_date: datetime
    expires_at: datetime
    hr_user_id: str
    hr_email: str

class OnboardingDetailsResponse(BaseModel):
    id: str
    candidate_email: str
    candidate_name: str
    position: str
    company_name: str
    status: OnboardingStatus
    sent_date: datetime
    expires_at: datetime
    hr_user_id: str
    hr_email: str
    candidate_details: Optional[Dict[str, Any]] = None
    submitted_at: Optional[datetime] = None
