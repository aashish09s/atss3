from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BusinessTypeModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    code: str  # e.g., TP, PM, CM, RE, TM, LR
    name: str  # e.g., Third-Party Payroll
    prefix: str  # e.g., TP
    default_tax_rate: float = 18.0
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

