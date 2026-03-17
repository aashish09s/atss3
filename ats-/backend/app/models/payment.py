from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PaymentModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    invoice_id: str
    invoice_number: str
    client_name: Optional[str] = None
    amount: float
    payment_date: datetime
    transaction_ref: Optional[str] = None
    remarks: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class PaymentCreate(BaseModel):
    amount: float
    payment_date: datetime
    transaction_ref: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True

