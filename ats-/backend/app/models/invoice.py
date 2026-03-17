from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId


class InvoiceLineItem(BaseModel):
    """Invoice line item model"""
    item_description: str
    sac_code: Optional[str] = None  # Service Accounting Code (legacy)
    business_unique_id: Optional[str] = None  # Generated per business selection
    rate_per_item: float
    quantity: int = 1
    taxable_value: float
    tax_rate: float = 18.0  # GST rate (default 18%)
    tax_amount: float
    amount: float


class InvoiceModel(BaseModel):
    """Invoice document model for MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    invoice_number: str  # Auto-generated, e.g., TP-1p / TP-1t
    jd_id: Optional[str] = None  # Job Description ID (optional for direct invoices)
    jd_unique_id: Optional[str] = None
    source: str = "jd"  # "jd" | "direct"

    # Business context
    business_type_code: Optional[str] = None  # e.g., third_party_payroll
    business_prefix: Optional[str] = None  # e.g., TP
    invoice_type: str = "tax"  # "tax" | "proforma"
    
    # Invoice dates
    invoice_date: datetime
    due_date: Optional[datetime] = None
    
    # Status
    status: str = "draft"  # "draft", "sent", "paid", "cancelled"
    
    # Company/Supplier Information (your company)
    company_name: Optional[str] = None
    company_gstin: Optional[str] = None
    company_pan: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_bank_name: Optional[str] = None
    company_bank_account: Optional[str] = None
    company_bank_ifsc: Optional[str] = None
    company_bank_branch: Optional[str] = None
    
    # Client/Customer Information
    client_name: str
    client_company_name: Optional[str] = None
    client_gstin: Optional[str] = None
    client_pan: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_billing_address: Optional[str] = None
    place_of_supply: Optional[str] = None
    
    # Invoice Items
    line_items: List[InvoiceLineItem] = []
    
    # Financial Summary
    subtotal: float = 0.0
    cgst_rate: float = 9.0  # CGST rate (half of total GST)
    sgst_rate: float = 9.0  # SGST rate (half of total GST)
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    total_tax: float = 0.0
    total_amount: float = 0.0
    tds_amount: float = 0.0  # Tax Deducted at Source
    
    # Additional details
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    
    # Metadata
    created_by: str  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

