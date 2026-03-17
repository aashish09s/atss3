from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.models.invoice import InvoiceModel, InvoiceLineItem
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import string
import random

router = APIRouter(prefix="/api/hr/invoices", tags=["Invoices"])


async def get_business_prefix(db, business_type_code: str) -> str:
    # Try DB first
    bt = await db.business_types.find_one({"code": business_type_code, "active": True})
    if bt and bt.get("prefix"):
        return bt.get("prefix")
    # Fallback to static map when collection is empty/not seeded
    fallback = {
        "third_party_payroll": "tpp",
        "payroll_mgmt": "pm",
        "compliance_mgmt": "cm",
        "recruitment": "rc",  # Changed from 'rec' to 'rc' as per user requirement
        "task_mgmt": "tm",
        "licensing_reg": "lr",
    }
    if business_type_code in fallback:
        return fallback[business_type_code]
    raise HTTPException(status_code=400, detail="Invalid business type")


async def next_sequence(db, key: str) -> int:
    doc = await db.counters.find_one_and_update(
        {"_id": key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return doc.get("seq", 1)


async def generate_business_invoice_number(db, business_type_code: str, invoice_type: str) -> str:
    prefix = await get_business_prefix(db, business_type_code)
    type_suffix = 't' if invoice_type == 'tax' else 'p'
    seq = await next_sequence(db, f"invoice_{prefix}_{invoice_type}")
    return f"{prefix}-{seq}{type_suffix}"


async def peek_next_business_invoice_number(db, business_type_code: str, invoice_type: str) -> str:
    """Return the next invoice number without incrementing the counter."""
    prefix = await get_business_prefix(db, business_type_code)
    type_suffix = 't' if invoice_type == 'tax' else 'p'
    doc = await db.counters.find_one({"_id": f"invoice_{prefix}_{invoice_type}"})
    current = (doc or {}).get("seq", 0)
    next_value = current + 1
    return f"{prefix}-{next_value}{type_suffix}"


class InvoiceCreateRequest(BaseModel):
    jd_id: Optional[str] = None
    invoice_date: datetime
    due_date: Optional[datetime] = None
    source: Optional[str] = "jd"  # jd | direct
    business_type_code: str  # e.g., third_party_payroll
    invoice_type: str = "tax"  # tax | proforma
    calculate_tax: bool = True  # Toggle to calculate tax or not
    
    # Company Information
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
    
    # Client Information
    client_name: str
    client_company_name: Optional[str] = None
    client_gstin: Optional[str] = None
    client_pan: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_billing_address: Optional[str] = None
    place_of_supply: Optional[str] = None
    
    # Invoice Items
    line_items: List[Dict[str, Any]] = []
    
    # Financial Summary
    subtotal: float = 0.0
    cgst_rate: float = 9.0
    sgst_rate: float = 9.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    total_tax: float = 0.0
    total_amount: float = 0.0
    tds_amount: float = 0.0  # Tax Deducted at Source
    
    # Additional details
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    jd_id: Optional[str] = None
    jd_unique_id: Optional[str] = None
    invoice_date: datetime
    due_date: Optional[datetime] = None
    status: str
    client_name: str
    source: Optional[str] = None
    total_amount: float
    created_at: datetime
    sent_at: Optional[datetime] = None


@router.post("/", response_model=InvoiceResponse)
async def create_or_save_invoice(
    invoice_data: InvoiceCreateRequest,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Create or save invoice (draft)"""
    db = await get_db()
    
    try:
        jd = None
        if invoice_data.source != "direct":
            if not invoice_data.jd_id:
                raise HTTPException(status_code=400, detail="jd_id is required for JD-sourced invoices")
            # Verify JD exists and belongs to user
            jd = await db.jds.find_one({
                "_id": ObjectId(invoice_data.jd_id),
                "uploaded_by": str(current_user["_id"]),
                "requirement_fulfilled": True
            })
            if not jd:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job description not found or not fulfilled"
                )
        
        # Generate per-business invoice number
        invoice_number = await generate_business_invoice_number(db, invoice_data.business_type_code, invoice_data.invoice_type)
        
        # Calculate due date if not provided (default: 30 days from invoice date)
        due_date = invoice_data.due_date
        if not due_date:
            due_date = invoice_data.invoice_date + timedelta(days=30)
        
        # Prepare line items
        line_items = []
        for item in invoice_data.line_items:
            line_items.append({
                "item_description": item.get("item_description", ""),
                "sac_code": item.get("sac_code"),
                "business_unique_id": item.get("business_unique_id"),
                "rate_per_item": item.get("rate_per_item", 0),
                "quantity": item.get("quantity", 1),
                "taxable_value": item.get("taxable_value", 0),
                "tax_rate": item.get("tax_rate", 18.0),
                "tax_amount": item.get("tax_amount", 0),
                "amount": item.get("amount", 0)
            })
        
        # Use calculate_tax toggle to determine if tax should be applied
        subtotal = invoice_data.subtotal
        cgst_rate = invoice_data.cgst_rate
        sgst_rate = invoice_data.sgst_rate
        cgst_amount = invoice_data.cgst_amount
        sgst_amount = invoice_data.sgst_amount
        total_tax = invoice_data.total_tax
        total_amount = invoice_data.total_amount
        # If calculate_tax is False, zero taxes and compute total as subtotal only
        if not invoice_data.calculate_tax:
            cgst_amount = 0.0
            sgst_amount = 0.0
            total_tax = 0.0
            total_amount = subtotal

        # Create invoice document
        invoice_doc = {
            "invoice_number": invoice_number,
            "jd_id": invoice_data.jd_id,
            "jd_unique_id": jd.get("jd_unique_id") if jd else None,
            "source": invoice_data.source or "jd",
            "business_type_code": invoice_data.business_type_code,
            "business_prefix": await get_business_prefix(db, invoice_data.business_type_code),
            "invoice_type": invoice_data.invoice_type,
            "invoice_date": invoice_data.invoice_date,
            "due_date": due_date,
            "status": "draft",
            "company_name": invoice_data.company_name,
            "company_gstin": invoice_data.company_gstin,
            "company_pan": invoice_data.company_pan,
            "company_address": invoice_data.company_address,
            "company_phone": invoice_data.company_phone,
            "company_email": invoice_data.company_email,
            "company_website": invoice_data.company_website,
            "company_bank_name": invoice_data.company_bank_name,
            "company_bank_account": invoice_data.company_bank_account,
            "company_bank_ifsc": invoice_data.company_bank_ifsc,
            "company_bank_branch": invoice_data.company_bank_branch,
            "client_name": invoice_data.client_name,
            "client_company_name": invoice_data.client_company_name,
            "client_gstin": invoice_data.client_gstin,
            "client_pan": invoice_data.client_pan,
            "client_email": invoice_data.client_email,
            "client_phone": invoice_data.client_phone,
            "client_billing_address": invoice_data.client_billing_address,
            "place_of_supply": invoice_data.place_of_supply,
            "line_items": line_items,
            "subtotal": subtotal,
            "cgst_rate": cgst_rate,
            "sgst_rate": sgst_rate,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "total_tax": total_tax,
            "total_amount": total_amount,
            "tds_amount": invoice_data.tds_amount if hasattr(invoice_data, 'tds_amount') else 0.0,
            "notes": invoice_data.notes,
            "terms_and_conditions": invoice_data.terms_and_conditions,
            "created_by": str(current_user["_id"]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.invoices.insert_one(invoice_doc)
        
        # Return created invoice
        created_invoice = await db.invoices.find_one({"_id": result.inserted_id})
        if not created_invoice:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created invoice"
            )
        return InvoiceResponse(
            id=str(created_invoice.get("_id", "")),
            invoice_number=created_invoice.get("invoice_number", ""),
            jd_id=created_invoice.get("jd_id"),
            jd_unique_id=created_invoice.get("jd_unique_id"),
            invoice_date=created_invoice.get("invoice_date", datetime.utcnow()),
            due_date=created_invoice.get("due_date"),
            status=created_invoice.get("status", "draft"),
            client_name=created_invoice.get("client_name", ""),
            source=created_invoice.get("source", "jd"),
            total_amount=created_invoice.get("total_amount", 0.0),
            created_at=created_invoice.get("created_at", datetime.utcnow()),
            sent_at=created_invoice.get("sent_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Send invoice via email"""
    db = await get_db()
    
    try:
        invoice_object_id = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    # Check if invoice exists - Admins and accountants can access any invoice, HR users see only their own
    invoice_query: Dict[str, Any] = {"_id": invoice_object_id}
    if current_user["role"] not in ["admin", "accountant"]:
        invoice_query["created_by"] = str(current_user["_id"])
    invoice = await db.invoices.find_one(invoice_query)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if not invoice.get("client_email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client email is required to send invoice"
        )
    
    try:
        # Generate invoice email HTML
        from app.services.invoice_email_service import generate_invoice_email_html, generate_invoice_pdf
        from app.services.email_service import send_email_with_attachment, send_email
        
        # Generate email HTML body
        email_body = generate_invoice_email_html(invoice)
        
        # Try to generate PDF invoice (optional - email will still be sent without it)
        pdf_data = None
        invoice_filename = f"Invoice_{invoice['invoice_number']}.pdf"
        
        try:
            pdf_data = await generate_invoice_pdf(invoice)
            print(f"[SUCCESS] PDF invoice generated successfully: {len(pdf_data)} bytes")
        except Exception as pdf_error:
            print(f"[WARNING] PDF generation failed: {str(pdf_error)}")
            print("[INFO] Proceeding to send email without PDF attachment")
            import traceback
            traceback.print_exc()
        
        # Send email with or without PDF attachment
        email_sent = False
        try:
            if pdf_data:
                # Send with PDF attachment
                print(f"[INFO] Attempting to send invoice email with PDF to {invoice['client_email']}")
                await send_email_with_attachment(
                    to_email=invoice["client_email"],
                    subject=f"Invoice {invoice['invoice_number']} - {invoice.get('company_name', 'Invoice')}",
                    body=email_body,
                    is_html=True,
                    from_name=invoice.get("company_name", "Invoice Department"),
                    from_email=invoice.get("company_email"),  # Will fallback to SMTP settings if None
                    reply_to=invoice.get("company_email"),
                    attach_pdf=pdf_data,
                    pdf_filename=invoice_filename
                )
                email_sent = True
                print(f"[SUCCESS] Invoice email with PDF sent successfully to {invoice['client_email']}")
            else:
                # Send without PDF attachment
                print(f"[INFO] Attempting to send invoice email (no PDF) to {invoice['client_email']}")
                await send_email(
                    to_email=invoice["client_email"],
                    subject=f"Invoice {invoice['invoice_number']} - {invoice.get('company_name', 'Invoice')}",
                    body=email_body,
                    is_html=True,
                    from_name=invoice.get("company_name", "Invoice Department"),
                    from_email=invoice.get("company_email"),  # Will fallback to SMTP settings if None
                    reply_to=invoice.get("company_email")
                )
                email_sent = True
                print(f"[SUCCESS] Invoice email sent successfully to {invoice['client_email']} (without PDF)")
        except Exception as email_error:
            print(f"[ERROR] Failed to send invoice email to {invoice['client_email']}: {str(email_error)}")
            import traceback
            traceback.print_exc()
            # DO NOT update status if email fails
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send invoice email: {str(email_error)}"
            )
        
        # Only update invoice status if email was successfully sent
        if email_sent:
            await db.invoices.update_one(
                {"_id": invoice_object_id},
                {"$set": {
                    "status": "sent",
                    "sent_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            print(f"[SUCCESS] Invoice status updated to 'sent' for invoice {invoice['invoice_number']}")
        
        # Return updated invoice
        updated_invoice = await db.invoices.find_one({"_id": invoice_object_id})
        if not updated_invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found after update"
            )
        return InvoiceResponse(
            id=str(updated_invoice.get("_id", "")),
            invoice_number=updated_invoice.get("invoice_number", ""),
            jd_id=updated_invoice.get("jd_id"),
            jd_unique_id=updated_invoice.get("jd_unique_id"),
            invoice_date=updated_invoice.get("invoice_date", datetime.utcnow()),
            due_date=updated_invoice.get("due_date"),
            status=updated_invoice.get("status", "draft"),
            client_name=updated_invoice.get("client_name", ""),
            source=updated_invoice.get("source", "jd"),
            total_amount=updated_invoice.get("total_amount", 0.0),
            created_at=updated_invoice.get("created_at", datetime.utcnow()),
            sent_at=updated_invoice.get("sent_at")
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invoice: {str(e)}"
        )


@router.get("/job/{jd_id}", response_model=Optional[InvoiceResponse])
async def get_invoice_by_jd(
    jd_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Get invoice for a specific job description"""
    db = await get_db()
    
    # Admins and accountants can see any invoice, HR users see only their own
    invoice_query: Dict[str, Any] = {"jd_id": jd_id}
    if current_user["role"] not in ["admin", "accountant"]:
        invoice_query["created_by"] = str(current_user["_id"])
    invoice = await db.invoices.find_one(invoice_query)
    
    if not invoice:
        return None
    
    return InvoiceResponse(
        id=str(invoice.get("_id", "")),
        invoice_number=invoice.get("invoice_number", ""),
        jd_id=invoice.get("jd_id"),
        jd_unique_id=invoice.get("jd_unique_id"),
        invoice_date=invoice.get("invoice_date", datetime.utcnow()),
        due_date=invoice.get("due_date"),
        status=invoice.get("status", "draft"),
        client_name=invoice.get("client_name", ""),
        source=invoice.get("source", "jd"),
        total_amount=invoice.get("total_amount", 0.0),
        created_at=invoice.get("created_at", datetime.utcnow()),
        sent_at=invoice.get("sent_at")
    )


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))):
    """List invoices for current user (or all invoices for admin)"""
    db = await get_db()
    # Admins and accountants can see all invoices, HR users see only their own
    query = {} if current_user["role"] in ["admin", "accountant"] else {"created_by": str(current_user["_id"])}
    cursor = db.invoices.find(query).sort("created_at", -1)
    items = []
    async for inv in cursor:
        try:
            items.append(InvoiceResponse(
                id=str(inv.get("_id", "")),
                invoice_number=inv.get("invoice_number", ""),
                jd_id=inv.get("jd_id"),
                jd_unique_id=inv.get("jd_unique_id"),
                invoice_date=inv.get("invoice_date", datetime.utcnow()),
                due_date=inv.get("due_date"),
                status=inv.get("status", "draft"),
                client_name=inv.get("client_name", ""),
                source=inv.get("source", "jd"),
                total_amount=inv.get("total_amount", 0.0),
                created_at=inv.get("created_at", datetime.utcnow()),
                sent_at=inv.get("sent_at")
            ))
        except Exception as e:
            # Log error but continue processing other invoices
            print(f"[ERROR] Failed to parse invoice {inv.get('_id')}: {str(e)}")
            continue
    return items


@router.get("/next-number", response_model=dict)
async def get_next_invoice_number(
    business_type_code: str,
    invoice_type: str = "tax",
):
    """Peek the next invoice number for the given business/type without consuming it."""
    db = await get_db()
    try:
        number = await peek_next_business_invoice_number(db, business_type_code, invoice_type)
        return {"invoice_number": number}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}", response_model=Dict[str, Any])
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Get full invoice details by ID"""
    db = await get_db()
    
    try:
        invoice_object_id = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    # Admins and accountants can see any invoice, HR users see only their own
    invoice_query: Dict[str, Any] = {"_id": invoice_object_id}
    if current_user["role"] not in ["admin", "accountant"]:
        invoice_query["created_by"] = str(current_user["_id"])
    invoice = await db.invoices.find_one(invoice_query)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Convert ObjectId to string
    invoice["id"] = str(invoice["_id"])
    invoice["_id"] = str(invoice["_id"])
    
    # Convert datetime fields to ISO strings for JSON serialization
    if invoice.get("invoice_date"):
        invoice["invoice_date"] = invoice["invoice_date"].isoformat() if hasattr(invoice["invoice_date"], "isoformat") else invoice["invoice_date"]
    if invoice.get("due_date"):
        invoice["due_date"] = invoice["due_date"].isoformat() if hasattr(invoice["due_date"], "isoformat") else invoice["due_date"]
    if invoice.get("created_at"):
        invoice["created_at"] = invoice["created_at"].isoformat() if hasattr(invoice["created_at"], "isoformat") else invoice["created_at"]
    if invoice.get("updated_at"):
        invoice["updated_at"] = invoice["updated_at"].isoformat() if hasattr(invoice["updated_at"], "isoformat") else invoice["updated_at"]
    if invoice.get("sent_at"):
        invoice["sent_at"] = invoice["sent_at"].isoformat() if hasattr(invoice["sent_at"], "isoformat") else invoice["sent_at"]
    
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceCreateRequest,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Update an existing invoice"""
    db = await get_db()
    
    try:
        invoice_object_id = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    # Verify invoice exists - Admins and accountants can access any invoice, HR users see only their own
    invoice_query: Dict[str, Any] = {"_id": invoice_object_id}
    if current_user["role"] not in ["admin", "accountant"]:
        invoice_query["created_by"] = str(current_user["_id"])
    invoice = await db.invoices.find_one(invoice_query)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Store old invoice data for comparison (needed for accountant change tracking)
    old_invoice = invoice.copy()
    
    # Check if this is an accountant editing a tax invoice (security feature)
    is_accountant_edit = current_user["role"] == "accountant"
    is_tax_invoice = invoice.get("invoice_type") == "tax"
    
    # Calculate due date if not provided
    due_date = invoice_data.due_date
    if not due_date:
        due_date = invoice_data.invoice_date + timedelta(days=30)
    
    # Prepare line items
    line_items = []
    for item in invoice_data.line_items:
        line_items.append({
            "item_description": item.get("item_description", ""),
            "sac_code": item.get("sac_code"),
            "business_unique_id": item.get("business_unique_id"),
            "rate_per_item": item.get("rate_per_item", 0),
            "quantity": item.get("quantity", 1),
            "taxable_value": item.get("taxable_value", 0),
            "tax_rate": item.get("tax_rate", 18.0),
            "tax_amount": item.get("tax_amount", 0),
            "amount": item.get("amount", 0)
        })
    
    # Use calculate_tax toggle to determine if tax should be applied
    subtotal = invoice_data.subtotal
    cgst_rate = invoice_data.cgst_rate
    sgst_rate = invoice_data.sgst_rate
    cgst_amount = invoice_data.cgst_amount
    sgst_amount = invoice_data.sgst_amount
    total_tax = invoice_data.total_tax
    total_amount = invoice_data.total_amount
    if not invoice_data.calculate_tax:
        cgst_amount = 0.0
        sgst_amount = 0.0
        total_tax = 0.0
        total_amount = subtotal
    
    # Update invoice document
    update_doc = {
        "invoice_date": invoice_data.invoice_date,
        "due_date": due_date,
        "business_type_code": invoice_data.business_type_code,
        "invoice_type": invoice_data.invoice_type,
        "company_name": invoice_data.company_name,
        "company_gstin": invoice_data.company_gstin,
        "company_pan": invoice_data.company_pan,
        "company_address": invoice_data.company_address,
        "company_phone": invoice_data.company_phone,
        "company_email": invoice_data.company_email,
        "company_website": invoice_data.company_website,
        "company_bank_name": invoice_data.company_bank_name,
        "company_bank_account": invoice_data.company_bank_account,
        "company_bank_ifsc": invoice_data.company_bank_ifsc,
        "company_bank_branch": invoice_data.company_bank_branch,
        "client_name": invoice_data.client_name,
        "client_company_name": invoice_data.client_company_name,
        "client_gstin": invoice_data.client_gstin,
        "client_pan": invoice_data.client_pan,
        "client_email": invoice_data.client_email,
        "client_phone": invoice_data.client_phone,
        "client_billing_address": invoice_data.client_billing_address,
        "place_of_supply": invoice_data.place_of_supply,
        "line_items": line_items,
        "subtotal": subtotal,
        "cgst_rate": cgst_rate,
        "sgst_rate": sgst_rate,
        "cgst_amount": cgst_amount,
        "sgst_amount": sgst_amount,
        "total_tax": total_tax,
        "total_amount": total_amount,
        "tds_amount": invoice_data.tds_amount if hasattr(invoice_data, 'tds_amount') else invoice.get("tds_amount", 0.0),
        "notes": invoice_data.notes,
        "terms_and_conditions": invoice_data.terms_and_conditions,
        "updated_at": datetime.utcnow()
    }
    
    await db.invoices.update_one(
        {"_id": invoice_object_id},
        {"$set": update_doc}
    )
    
    # Security feature: If accountant edited a tax invoice, notify the admin who created this accountant
    if is_accountant_edit and is_tax_invoice:
        try:
            # Get accountant user details
            accountant_user = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
            if accountant_user and accountant_user.get("created_by_admin_id"):
                # Find the admin who created this accountant
                admin_user = await db.users.find_one({"_id": ObjectId(accountant_user["created_by_admin_id"])})
                if admin_user and admin_user.get("email"):
                    # Track changes between old and new invoice
                    changes = []
                    
                    # Compare key fields
                    fields_to_compare = [
                        ("invoice_date", "Invoice Date"),
                        ("due_date", "Due Date"),
                        ("client_name", "Client Name"),
                        ("client_email", "Client Email"),
                        ("client_company_name", "Client Company"),
                        ("client_gstin", "Client GSTIN"),
                        ("client_pan", "Client PAN"),
                        ("client_phone", "Client Phone"),
                        ("client_billing_address", "Client Billing Address"),
                        ("company_name", "Company Name"),
                        ("company_gstin", "Company GSTIN"),
                        ("company_pan", "Company PAN"),
                        ("company_email", "Company Email"),
                        ("place_of_supply", "Place of Supply"),
                        ("subtotal", "Subtotal"),
                        ("cgst_rate", "CGST Rate"),
                        ("sgst_rate", "SGST Rate"),
                        ("cgst_amount", "CGST Amount"),
                        ("sgst_amount", "SGST Amount"),
                        ("total_tax", "Total Tax"),
                        ("total_amount", "Total Amount"),
                        ("tds_amount", "TDS Amount"),
                        ("notes", "Notes"),
                        ("terms_and_conditions", "Terms and Conditions"),
                    ]
                    
                    for field_key, field_label in fields_to_compare:
                        old_value = old_invoice.get(field_key)
                        new_value = update_doc.get(field_key)
                        
                        # Handle datetime fields
                        if isinstance(old_value, datetime):
                            old_value = old_value.strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(new_value, datetime):
                            new_value = new_value.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Compare values (handle None and empty string as equivalent)
                        old_str = str(old_value) if old_value is not None else ""
                        new_str = str(new_value) if new_value is not None else ""
                        
                        if old_str != new_str:
                            changes.append({
                                "field": field_label,
                                "old_value": old_str if old_str else "(empty)",
                                "new_value": new_str if new_str else "(empty)"
                            })
                    
                    # Compare line items (simplified - just check count and total)
                    old_line_items = old_invoice.get("line_items", [])
                    new_line_items = update_doc.get("line_items", [])
                    if len(old_line_items) != len(new_line_items):
                        changes.append({
                            "field": "Line Items Count",
                            "old_value": str(len(old_line_items)),
                            "new_value": str(len(new_line_items))
                        })
                    
                    # Only send email if there are actual changes
                    if changes:
                        # Generate email HTML
                        email_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                                .header {{ background: #7c3aed; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                                .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                                .section {{ margin: 20px 0; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #7c3aed; }}
                                .change-item {{ margin: 10px 0; padding: 10px; background: #fef3c7; border-radius: 5px; }}
                                .field-name {{ font-weight: bold; color: #7c3aed; }}
                                .old-value {{ color: #dc2626; text-decoration: line-through; }}
                                .new-value {{ color: #059669; font-weight: bold; }}
                                .accountant-info {{ background: #e0e7ff; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                                .footer {{ margin-top: 20px; padding: 15px; background: #f3f4f6; border-radius: 0 0 8px 8px; font-size: 12px; color: #6b7280; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h2>🔒 Security Alert: Tax Invoice Edited by Accountant</h2>
                                </div>
                                <div class="content">
                                    <div class="section">
                                        <h3>Invoice Details</h3>
                                        <p><strong>Invoice ID:</strong> {invoice.get('invoice_number', 'N/A')}</p>
                                        <p><strong>Client Name:</strong> {invoice.get('client_name', 'N/A')}</p>
                                        <p><strong>Invoice Date:</strong> {(invoice.get('invoice_date').strftime('%Y-%m-%d') if isinstance(invoice.get('invoice_date'), datetime) else str(invoice.get('invoice_date', 'N/A')))}</p>
                                        <p><strong>Total Amount (Before Changes):</strong> ₹{invoice.get('total_amount', 0):,.2f}</p>
                                        <p><strong>Total Amount (After Changes):</strong> ₹{update_doc.get('total_amount', 0):,.2f}</p>
                                    </div>
                                    
                                    <div class="accountant-info">
                                        <h3>Accountant Information</h3>
                                        <p><strong>Username:</strong> {accountant_user.get('username', 'N/A')}</p>
                                        <p><strong>Email:</strong> {accountant_user.get('email', 'N/A')}</p>
                                        <p><strong>Full Name:</strong> {accountant_user.get('full_name', 'N/A')}</p>
                                        <p><strong>Edit Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                                    </div>
                                    
                                    <div class="section">
                                        <h3>Changes Made</h3>
                                        <p>The following changes were made to the tax invoice:</p>
                                        {"".join([
                                            f'''
                                            <div class="change-item">
                                                <span class="field-name">{change["field"]}:</span><br>
                                                <span class="old-value">Old: {change["old_value"]}</span><br>
                                                <span class="new-value">New: {change["new_value"]}</span>
                                            </div>
                                            ''' for change in changes
                                        ])}
                                    </div>
                                    
                                    <div class="footer">
                                        <p>This is an automated security notification. Please review the changes made to the invoice.</p>
                                        <p>If you did not authorize these changes, please contact the system administrator immediately.</p>
                                    </div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Send email to admin
                        from app.services.email_service import send_email
                        try:
                            await send_email(
                                to_email=admin_user["email"],
                                subject=f"Security Alert: Tax Invoice {invoice.get('invoice_number', 'N/A')} Edited by Accountant",
                                body=email_html,
                                is_html=True,
                                from_name="SynHireOne Security System",
                                from_email=invoice.get("company_email") or None
                            )
                            print(f"[SECURITY] Successfully sent change notification email to admin {admin_user['email']} for invoice {invoice.get('invoice_number')}")
                        except Exception as email_error:
                            # Log error but don't fail the invoice update
                            print(f"[ERROR] Failed to send security notification email to admin: {str(email_error)}")
                            import traceback
                            traceback.print_exc()
        except Exception as security_error:
            # Log error but don't fail the invoice update
            print(f"[ERROR] Failed to process security notification: {str(security_error)}")
            import traceback
            traceback.print_exc()
    
    # Return updated invoice
    updated_invoice = await db.invoices.find_one({"_id": invoice_object_id})
    if not updated_invoice:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated invoice"
        )
    
    return InvoiceResponse(
        id=str(updated_invoice.get("_id", "")),
        invoice_number=updated_invoice.get("invoice_number", ""),
        jd_id=updated_invoice.get("jd_id"),
        jd_unique_id=updated_invoice.get("jd_unique_id"),
        invoice_date=updated_invoice.get("invoice_date", datetime.utcnow()),
        due_date=updated_invoice.get("due_date"),
        status=updated_invoice.get("status", "draft"),
        client_name=updated_invoice.get("client_name", ""),
        source=updated_invoice.get("source", "jd"),
        total_amount=updated_invoice.get("total_amount", 0.0),
        created_at=updated_invoice.get("created_at", datetime.utcnow()),
        sent_at=updated_invoice.get("sent_at")
    )


class TDSUpdateRequest(BaseModel):
    tds_amount: float = 0.0


@router.patch("/{invoice_id}/tds", response_model=dict)
async def update_invoice_tds(
    invoice_id: str,
    tds_data: TDSUpdateRequest,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Update TDS amount for an invoice"""
    db = await get_db()
    
    # Verify invoice exists - Admins and accountants can access any invoice, HR users see only their own
    invoice_query: Dict[str, Any] = {"_id": ObjectId(invoice_id)}
    if current_user["role"] not in ["admin", "accountant"]:
        invoice_query["created_by"] = str(current_user["_id"])
    invoice = await db.invoices.find_one(invoice_query)
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    tds_amount = float(tds_data.tds_amount) if tds_data.tds_amount else 0.0
    
    # Update TDS amount
    await db.invoices.update_one(
        {"_id": ObjectId(invoice_id)},
        {
            "$set": {
                "tds_amount": tds_amount,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"success": True, "invoice_id": invoice_id, "tds_amount": tds_amount}

