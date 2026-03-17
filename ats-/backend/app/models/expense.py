from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ExpenseModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    category: str
    title: Optional[str] = None
    amount: float
    paid_amount: float = 0.0  # Amount paid for this expense
    date: datetime
    notes: Optional[str] = None
    recurring: bool = False
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

