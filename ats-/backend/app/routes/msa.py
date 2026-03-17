from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.core.config import settings
from app.services.email_service import send_email_with_attachment, send_email
from app.services.storage import storage_service
import secrets
import hashlib
import os
import tempfile
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


hr_router = APIRouter(prefix="/api/hr/msa", tags=["MSA"])
public_router = APIRouter(prefix="/api/msa", tags=["MSA Public"])


class MSAListItem(BaseModel):
    id: str
    recipient_name: str
    recipient_email: EmailStr
    agreement_type: str
    agreement_title: str
    company_name: str
    status: str
    created_at: datetime
    signed_at: Optional[datetime]
    signed_pdf_url: Optional[str]


class MSATemplateCreate(BaseModel):
    template_name: str
    agreement_type: str  # 'client' or 'candidate'
    agreement_title: str
    agreement_content: str


class MSATemplateResponse(BaseModel):
    id: str
    template_name: str
    agreement_type: str
    agreement_title: str
    agreement_content: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]


class MSAPublicResponse(BaseModel):
    recipient_name: str
    recipient_email: EmailStr
    agreement_title: str
    agreement_content: str
    company_name: str
    company_signer_name: Optional[str]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _strip_html(raw_html: str) -> str:
    """Remove HTML tags and decode entities."""
    html = raw_html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    html = html.replace("</p>", "\n").replace("</div>", "\n")
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    return text.strip()


def _generate_msa_pdf(
    agreement_content: str,
    agreement_title: str,
    recipient_name: str,
    recipient_signature_path: Optional[str],
    recipient_signed_name: str,
    company_name: str,
    company_signer_name: str,
    company_signature_path: Optional[str],
    company_stamp_path: Optional[str],
    company_logo_path: Optional[str] = None,
    company_address: Optional[str] = None,
    company_gst: Optional[str] = None,
    header_color: str = "#1F2937",
) -> (str, bytes):
    """Generate a signed MSA PDF with both party signatures."""
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.close()

    doc = SimpleDocTemplate(
        temp_pdf.name,
        pagesize=letter,
        leftMargin=0,
        rightMargin=0,
        topMargin=0,
        bottomMargin=50,
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "MSATitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1F2937"),
        alignment=1,
        spaceAfter=20,
    )
    
    body_style = ParagraphStyle(
        "MSABody",
        parent=styles["BodyText"],
        fontSize=11,
        textColor=colors.HexColor("#374151"),
        leading=16,
        spaceAfter=12,
    )
    
    heading_style = ParagraphStyle(
        "MSAHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=10,
        spaceBefore=15,
    )

    story = []

    # Professional Header (like the image)
    try:
        header_bg_color = colors.HexColor(header_color) if header_color.startswith('#') else colors.HexColor("#1F2937")
    except:
        header_bg_color = colors.HexColor("#1F2937")
    
    # Create header data
    header_data = []
    
    # Left side: Logo
    left_content = []
    if company_logo_path:
        try:
            logo_img = Image(company_logo_path, width=1.2 * inch, height=1.2 * inch)
            left_content.append(logo_img)
        except Exception:
            pass
    
    # Right side: Company info
    right_content = []
    company_info_style = ParagraphStyle(
        "CompanyInfo",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.white,
        alignment=1,  # Center
        leading=14,
    )
    
    if company_name:
        right_content.append(Paragraph(f"<b>{company_name.upper()}</b>", 
            ParagraphStyle("CompanyName", parent=company_info_style, fontSize=14, spaceBefore=6)))
    
    if company_address:
        right_content.append(Paragraph(company_address, company_info_style))
    
    if company_gst:
        right_content.append(Paragraph(f"The Corporate Identity Number of the company is {company_gst}", 
            company_info_style))
    
    # Create header table with no margins (full width)
    if left_content or right_content:
        # Get full page width (letter size = 8.5 inches)
        page_width = letter[0]
        header_table_data = [[left_content, right_content]]
        header_table = Table(header_table_data, colWidths=[2*inch, page_width-2*inch])
        header_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), header_bg_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 30),
                ("RIGHTPADDING", (1, 0), (1, -1), 30),
                ("TOPPADDING", (0, 0), (-1, -1), 20),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 0))
    
    # After header, add a spacer for content
    story.append(Spacer(1, 30))
    
    # Title with left margin
    title_with_margin = ParagraphStyle(
        "TitleMargin",
        parent=title_style,
        leftIndent=50,
        rightIndent=50,
    )
    story.append(Paragraph(f"<b>{agreement_title}</b>", title_with_margin))
    story.append(Spacer(1, 20))

    # Agreement content with margins
    body_with_margin = ParagraphStyle(
        "BodyMargin",
        parent=body_style,
        leftIndent=50,
        rightIndent=50,
    )
    
    cleaned_content = _strip_html(agreement_content)
    paragraphs = cleaned_content.split('\n')
    
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), body_with_margin))
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 30))

    # Signature section with margins
    heading_with_margin = ParagraphStyle(
        "HeadingMargin",
        parent=heading_style,
        leftIndent=50,
        rightIndent=50,
    )
    story.append(Paragraph("<b>SIGNATURES</b>", heading_with_margin))
    story.append(Spacer(1, 15))

    # Create two-column signature table
    sig_data = []
    
    # Company signature column
    company_col = []
    if company_signature_path:
        try:
            company_sig_img = Image(company_signature_path, width=2.2 * inch, height=0.9 * inch)
            company_col.append(company_sig_img)
        except Exception:
            company_col.append(Paragraph("[Signature]", body_style))
    else:
        company_col.append(Paragraph("_____________________", body_style))
    
    company_col.append(Spacer(1, 5))
    company_col.append(Paragraph(f"<b>{company_signer_name or company_name}</b>", body_style))
    company_col.append(Paragraph(company_name, body_style))
    company_col.append(Paragraph(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", body_style))
    
    if company_stamp_path:
        try:
            company_stamp_img = Image(company_stamp_path, width=1.2 * inch, height=1.2 * inch)
            company_col.append(Spacer(1, 5))
            company_col.append(company_stamp_img)
        except Exception:
            pass

    # Recipient signature column
    recipient_col = []
    if recipient_signature_path:
        try:
            recipient_sig_img = Image(recipient_signature_path, width=2.2 * inch, height=0.9 * inch)
            recipient_col.append(recipient_sig_img)
        except Exception:
            recipient_col.append(Paragraph("[Signature]", body_style))
    else:
        recipient_col.append(Paragraph("_____________________", body_style))
    
    recipient_col.append(Spacer(1, 5))
    recipient_col.append(Paragraph(f"<b>{recipient_signed_name}</b>", body_style))
    recipient_col.append(Paragraph(recipient_name, body_style))
    recipient_col.append(Paragraph(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", body_style))

    # Create table with two columns (with page margins considered)
    content_width = letter[0] - 100  # 50px margin on each side
    sig_table = Table(
        [[company_col, recipient_col]],
        colWidths=[content_width * 0.5, content_width * 0.5],
    )
    sig_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 50),
                ("LEFTPADDING", (1, 0), (1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 50),
            ]
        )
    )
    story.append(sig_table)

    doc.build(story)

    with open(temp_pdf.name, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    return temp_pdf.name, pdf_bytes


def _local_path_from_filename(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    return os.path.join(os.path.abspath(settings.local_upload_dir), filename)


async def _save_upload_to_temp(upload: UploadFile) -> Optional[str]:
    if not upload:
        return None
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.filename)[1])
    temp_file.write(await upload.read())
    temp_file.close()
    return temp_file.name


@hr_router.post("/initiate")
async def initiate_msa(
    recipient_name: str = Form(...),
    recipient_email: EmailStr = Form(...),
    agreement_type: str = Form(...),  # 'client' or 'candidate'
    agreement_title: str = Form(...),
    agreement_content: str = Form(...),
    company_name: str = Form(...),
    company_signer_name: str = Form(None),
    company_signer_email: EmailStr = Form(None),
    company_signature: UploadFile = File(None),
    company_stamp: UploadFile = File(None),
    company_logo: UploadFile = File(None),
    company_address: str = Form(""),
    company_gst: str = Form(""),
    header_color: str = Form("#1F2937"),
    verification_method: str = Form("esign"),  # NEW: 'esign' or 'otp'
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """Initiate MSA and send e-signature link or OTP to recipient."""
    db = await get_db()
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    
    # Generate OTP if verification method is OTP
    otp_code = None
    if verification_method == "otp":
        otp_code = str(secrets.randbelow(1000000)).zfill(6)  # 6-digit OTP

    # Save company logo, signature and stamp
    company_logo_temp = await _save_upload_to_temp(company_logo) if company_logo else None
    company_sig_temp = await _save_upload_to_temp(company_signature) if company_signature else None
    company_stamp_temp = await _save_upload_to_temp(company_stamp) if company_stamp else None

    company_logo_url = None
    company_logo_filename = None
    if company_logo_temp and company_logo:
        company_logo_url = await storage_service.save_file(
            company_logo_temp, f"msa/company/logos/{company_logo.filename or 'logo.png'}"
        )
        if company_logo_url and "/uploads/" in company_logo_url:
            company_logo_filename = company_logo_url.split("/uploads/")[1]
        else:
            company_logo_filename = company_logo_url

    company_sig_url = None
    company_sig_filename = None
    if company_sig_temp and company_signature:
        company_sig_url = await storage_service.save_file(
            company_sig_temp, f"msa/company/signatures/{company_signature.filename or 'signature.png'}"
        )
        if company_sig_url and "/uploads/" in company_sig_url:
            company_sig_filename = company_sig_url.split("/uploads/")[1]
        else:
            company_sig_filename = company_sig_url

    company_stamp_url = None
    company_stamp_filename = None
    if company_stamp_temp and company_stamp:
        company_stamp_url = await storage_service.save_file(
            company_stamp_temp, f"msa/company/stamps/{company_stamp.filename or 'stamp.png'}"
        )
        if company_stamp_url and "/uploads/" in company_stamp_url:
            company_stamp_filename = company_stamp_url.split("/uploads/")[1]
        else:
            company_stamp_filename = company_stamp_url

    # Clean up temp files
    for temp_file in [company_logo_temp, company_sig_temp, company_stamp_temp]:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

    # Store MSA in database
    doc = {
        "recipient_name": recipient_name,
        "recipient_email": recipient_email,
        "agreement_type": agreement_type,
        "agreement_title": agreement_title,
        "agreement_content": agreement_content,
        "company_name": company_name,
        "company_signer_name": company_signer_name,
        "company_signer_email": company_signer_email,
        "company_logo_url": company_logo_url,
        "company_logo_filename": company_logo_filename,
        "company_address": company_address,
        "company_gst": company_gst,
        "header_color": header_color,
        "company_signature_url": company_sig_url,
        "company_signature_filename": company_sig_filename,
        "company_stamp_url": company_stamp_url,
        "company_stamp_filename": company_stamp_filename,
        "status": "pending",
        "signature_token_hash": token_hash,
        "token_expires_at": now + timedelta(days=30),
        "created_at": now,
        "updated_at": now,
        "created_by": str(current_user["_id"]),
        "signed_at": None,
        "signed_pdf_url": None,
        "verification_method": verification_method,  # NEW
        "otp_code": otp_code,  # NEW: Store OTP if method is OTP
        "otp_verified": False if verification_method == "otp" else None,  # NEW: Track OTP verification
    }

    result = await db.msa.insert_one(doc)
    record_id = str(result.inserted_id)

    # Send email with signature link or OTP
    signature_link = f"{settings.frontend_base_url.rstrip('/')}/msa-sign/{token}"
    
    if verification_method == "otp":
        # OTP-based verification email
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1F2937;">Master Service Agreement - OTP Verification</h2>
            <p>Dear {recipient_name},</p>
            <p>You have received a Master Service Agreement from {company_name} that requires your verification.</p>
            <p><strong>Agreement:</strong> {agreement_title}</p>
            
            <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <p style="margin: 0 0 10px 0; font-size: 14px; color: #6B7280;">Your Verification Code:</p>
                <p style="margin: 0; font-size: 32px; font-weight: bold; color: #4F46E5; letter-spacing: 8px; font-family: monospace;">
                    {otp_code}
                </p>
            </div>
            
            <div style="margin: 30px 0; text-align: center;">
                <a href="{signature_link}" 
                   style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; font-weight: 600;">
                    Review Agreement & Enter Code
                </a>
            </div>
            <p style="color: #EF4444; font-weight: 600; text-align: center;">⚠️ Do not share this code with anyone.</p>
            <p style="color: #6B7280; font-size: 14px;">
                This verification code will expire in 30 days. If you have any questions, please contact {company_signer_email or company_name}.
            </p>
            <p style="color: #6B7280; font-size: 12px; margin-top: 20px;">
                If the button doesn't work, copy and paste this link into your browser:<br/>
                {signature_link}
            </p>
        </div>
        """
        email_subject = f"MSA: {agreement_title} - OTP Verification Required"
    else:
        # E-signature based verification email
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1F2937;">Master Service Agreement</h2>
            <p>Dear {recipient_name},</p>
            <p>You have received a Master Service Agreement from {company_name} that requires your signature.</p>
            <p><strong>Agreement:</strong> {agreement_title}</p>
            <div style="margin: 30px 0; text-align: center;">
                <a href="{signature_link}" 
                   style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; font-weight: 600;">
                    Review & Sign Agreement
                </a>
            </div>
            <p style="color: #6B7280; font-size: 14px;">
                This link will expire in 30 days. If you have any questions, please contact {company_signer_email or company_name}.
            </p>
            <p style="color: #6B7280; font-size: 12px; margin-top: 20px;">
                If the button doesn't work, copy and paste this link into your browser:<br/>
                {signature_link}
            </p>
        </div>
        """
        email_subject = f"MSA: {agreement_title} - Signature Required"

    await send_email(
        to_email=recipient_email,
        subject=email_subject,
        body=email_body,
        is_html=True,
    )

    return {
        "message": "MSA sent successfully with e-signature link",
        "record_id": record_id,
        "signature_link": signature_link,
    }


@hr_router.get("/", response_model=List[MSAListItem])
async def list_msa(
    type: Optional[str] = None,
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """List all MSA agreements."""
    db = await get_db()
    query = {}
    
    if current_user["role"] != "admin":
        query["created_by"] = str(current_user["_id"])
    
    if type:
        query["agreement_type"] = type

    records = await db.msa.find(query).sort("created_at", -1).to_list(None)

    items = []
    for record in records:
        items.append(
            MSAListItem(
                id=str(record["_id"]),
                recipient_name=record.get("recipient_name"),
                recipient_email=record.get("recipient_email"),
                agreement_type=record.get("agreement_type"),
                agreement_title=record.get("agreement_title"),
                company_name=record.get("company_name"),
                status=record.get("status"),
                created_at=record.get("created_at"),
                signed_at=record.get("signed_at"),
                signed_pdf_url=record.get("signed_pdf_url"),
            )
        )

    return items


@public_router.get("/{token}", response_model=MSAPublicResponse)
async def get_msa(token: str):
    """Get MSA details for signing."""
    db = await get_db()
    token_hash = _hash_token(token)

    record = await db.msa.find_one({"signature_token_hash": token_hash})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MSA not found")

    if record.get("status") == "signed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MSA already signed")

    expires_at = _normalize_datetime(record.get("token_expires_at"))
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="MSA link has expired")

    return {
        "recipient_name": record.get("recipient_name"),
        "recipient_email": record.get("recipient_email"),
        "agreement_title": record.get("agreement_title"),
        "agreement_content": record.get("agreement_content"),
        "company_name": record.get("company_name"),
        "company_signer_name": record.get("company_signer_name"),
        "verification_method": record.get("verification_method", "esign"),  # NEW
        "status": record.get("status"),  # NEW
    }


@public_router.post("/{token}/verify-otp")
async def verify_otp_msa(token: str, otp_code: str = Form(...)):
    """Verify OTP for MSA approval."""
    db = await get_db()
    token_hash = _hash_token(token)

    record = await db.msa.find_one({"signature_token_hash": token_hash})
    if not record:
        raise HTTPException(status_code=404, detail="MSA record not found")

    # Check if already signed
    if record.get("status") == "signed":
        raise HTTPException(status_code=409, detail="MSA already signed")

    # Check token expiration
    token_expires_at = record.get("token_expires_at")
    if token_expires_at:
        if token_expires_at.tzinfo is None:
            token_expires_at = token_expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > token_expires_at:
            raise HTTPException(status_code=410, detail="MSA link has expired")

    # Verify that this MSA uses OTP verification
    if record.get("verification_method") != "otp":
        raise HTTPException(status_code=400, detail="This MSA does not use OTP verification")

    # Verify OTP code
    if record.get("otp_code") != otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Mark MSA as signed
    await db.msa.update_one(
        {"_id": record["_id"]},
        {
            "$set": {
                "status": "signed",
                "signed_at": datetime.now(timezone.utc),
                "otp_verified": True,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    # Send confirmation emails
    recipient_subject = f"MSA Verified: {record.get('agreement_title')}"
    recipient_body = f"""
    <p>Dear {record.get('recipient_name')},</p>
    <p>Your verification for the Master Service Agreement has been successfully completed.</p>
    <p><strong>Agreement:</strong> {record.get('agreement_title')}</p>
    <p><strong>Company:</strong> {record.get('company_name')}</p>
    <p><strong>Verified on:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
    <p>Thank you for your confirmation.</p>
    <p>Best regards,<br>{record.get('company_name')}</p>
    """

    await send_email(
        to_email=record.get("recipient_email"),
        subject=recipient_subject,
        body=recipient_body,
        is_html=True,
    )

    # Notify company
    if record.get("company_signer_email"):
        company_subject = f"MSA Verified by {record.get('recipient_name')}"
        company_body = f"""
        <p>Dear {record.get('company_signer_name') or 'Team'},</p>
        <p>The Master Service Agreement has been verified by {record.get('recipient_name')} via OTP.</p>
        <p><strong>Agreement:</strong> {record.get('agreement_title')}</p>
        <p><strong>Verified on:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
        <p>Best regards,<br>System</p>
        """

        await send_email(
            to_email=record.get("company_signer_email"),
            subject=company_subject,
            body=company_body,
            is_html=True,
        )

    return {
        "message": "MSA verified successfully via OTP",
        "status": "signed",
    }


@public_router.post("/{token}/sign")
async def sign_msa(
    token: str,
    full_name: str = Form(...),
    signature: UploadFile = File(...),
):
    """Sign the MSA agreement."""
    db = await get_db()
    token_hash = _hash_token(token)

    record = await db.msa.find_one({"signature_token_hash": token_hash})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MSA not found")

    if record.get("status") == "signed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MSA already signed")

    expires_at = _normalize_datetime(record.get("token_expires_at"))
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="MSA link has expired")

    # Save recipient signature
    signature_temp = await _save_upload_to_temp(signature)
    signature_url = None
    signature_filename = None
    
    if signature_temp:
        signature_url = await storage_service.save_file(
            signature_temp, f"msa/recipient/signatures/{signature.filename or 'signature.png'}"
        )
        if signature_url and "/uploads/" in signature_url:
            signature_filename = signature_url.split("/uploads/")[1]
        else:
            signature_filename = signature_url

    # Get company logo, signature and stamp paths
    company_logo_local = _local_path_from_filename(record.get("company_logo_filename"))
    company_sig_local = _local_path_from_filename(record.get("company_signature_filename"))
    company_stamp_local = _local_path_from_filename(record.get("company_stamp_filename"))

    # Generate signed PDF
    pdf_path, pdf_bytes = _generate_msa_pdf(
        agreement_content=record.get("agreement_content", ""),
        agreement_title=record.get("agreement_title", ""),
        recipient_name=record.get("recipient_name", ""),
        recipient_signature_path=signature_temp,
        recipient_signed_name=full_name,
        company_name=record.get("company_name", ""),
        company_signer_name=record.get("company_signer_name", ""),
        company_signature_path=company_sig_local,
        company_stamp_path=company_stamp_local,
        company_logo_path=company_logo_local,
        company_address=record.get("company_address"),
        company_gst=record.get("company_gst"),
        header_color=record.get("header_color", "#1F2937"),
    )

    pdf_url = await storage_service.save_file(pdf_path, f"msa/signed/{record.get('_id')}.pdf")

    # Clean up temp files
    for path in [signature_temp, pdf_path]:
        if path and os.path.exists(path):
            os.remove(path)

    now = datetime.now(timezone.utc)
    await db.msa.update_one(
        {"_id": record["_id"]},
        {
            "$set": {
                "status": "signed",
                "signed_at": now,
                "signed_by_name": full_name,
                "signed_pdf_url": pdf_url,
                "recipient_signature_url": signature_url,
                "recipient_signature_filename": signature_filename,
                "updated_at": now,
            }
        },
    )

    # Send confirmation emails
    # To recipient
    recipient_subject = f"MSA Signed - {record.get('agreement_title')}"
    recipient_body = f"""
    <p>Dear {record.get('recipient_name')},</p>
    <p>Your signature has been successfully received for the Master Service Agreement.</p>
    <p><strong>Agreement:</strong> {record.get('agreement_title')}</p>
    <p>The signed agreement is attached for your records.</p>
    <p>Best regards,<br>{record.get('company_name')}</p>
    """
    
    await send_email_with_attachment(
        to_email=record.get("recipient_email"),
        subject=recipient_subject,
        body=recipient_body,
        is_html=True,
        attach_pdf=pdf_bytes,
        pdf_filename=f"Signed_MSA_{record.get('recipient_name').replace(' ', '_')}.pdf",
    )

    # To company
    if record.get("company_signer_email"):
        company_subject = f"MSA Signed by {record.get('recipient_name')}"
        company_body = f"""
        <p>Dear {record.get('company_signer_name') or 'Team'},</p>
        <p>The Master Service Agreement has been signed by {record.get('recipient_name')}.</p>
        <p><strong>Agreement:</strong> {record.get('agreement_title')}</p>
        <p><strong>Signed by:</strong> {full_name}</p>
        <p><strong>Signed on:</strong> {now.strftime('%Y-%m-%d %H:%M UTC')}</p>
        <p>The signed agreement is attached for your records.</p>
        """
        
        await send_email_with_attachment(
            to_email=record.get("company_signer_email"),
            subject=company_subject,
            body=company_body,
            is_html=True,
            attach_pdf=pdf_bytes,
            pdf_filename=f"Signed_MSA_{record.get('recipient_name').replace(' ', '_')}.pdf",
        )

    return {
        "message": "MSA signed successfully and confirmation emails sent",
        "signed_pdf_url": pdf_url,
    }



# ============================================
# MSA TEMPLATE MANAGEMENT ROUTES
# ============================================

@hr_router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_msa_template(
    template: MSATemplateCreate,
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """Create a new MSA template."""
    db = await get_db()
    now = datetime.now(timezone.utc)
    
    template_doc = {
        "template_name": template.template_name,
        "agreement_type": template.agreement_type,
        "agreement_title": template.agreement_title,
        "agreement_content": template.agreement_content,
        "created_by": current_user["user_id"],
        "created_at": now,
        "updated_at": now,
    }
    
    result = await db.msa_templates.insert_one(template_doc)
    template_doc["_id"] = result.inserted_id
    
    return {
        "success": True,
        "message": "MSA template created successfully",
        "template_id": str(result.inserted_id),
    }


@hr_router.get("/templates", response_model=List[MSATemplateResponse])
async def list_msa_templates(
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """List all MSA templates."""
    db = await get_db()
    
    # Show all templates for admin/superadmin, only user's own for hr/accountant
    if current_user["role"] in ["admin", "superadmin"]:
        templates = await db.msa_templates.find().sort("created_at", -1).to_list(100)
    else:
        templates = await db.msa_templates.find(
            {"created_by": current_user["user_id"]}
        ).sort("created_at", -1).to_list(100)
    
    return [
        MSATemplateResponse(
            id=str(t["_id"]),
            template_name=t["template_name"],
            agreement_type=t["agreement_type"],
            agreement_title=t["agreement_title"],
            agreement_content=t["agreement_content"],
            created_by=t["created_by"],
            created_at=t["created_at"],
            updated_at=t.get("updated_at"),
        )
        for t in templates
    ]


@hr_router.get("/templates/{template_id}")
async def get_msa_template(
    template_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """Get a specific MSA template."""
    db = await get_db()
    
    try:
        template = await db.msa_templates.find_one({"_id": ObjectId(template_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permission
    if current_user["role"] not in ["admin", "superadmin"]:
        if template["created_by"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return MSATemplateResponse(
        id=str(template["_id"]),
        template_name=template["template_name"],
        agreement_type=template["agreement_type"],
        agreement_title=template["agreement_title"],
        agreement_content=template["agreement_content"],
        created_by=template["created_by"],
        created_at=template["created_at"],
        updated_at=template.get("updated_at"),
    )


@hr_router.put("/templates/{template_id}")
async def update_msa_template(
    template_id: str,
    template: MSATemplateCreate,
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """Update an MSA template."""
    db = await get_db()
    
    try:
        existing = await db.msa_templates.find_one({"_id": ObjectId(template_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permission
    if current_user["role"] not in ["admin", "superadmin"]:
        if existing["created_by"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    now = datetime.now(timezone.utc)
    update_doc = {
        "template_name": template.template_name,
        "agreement_type": template.agreement_type,
        "agreement_title": template.agreement_title,
        "agreement_content": template.agreement_content,
        "updated_at": now,
    }
    
    await db.msa_templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": update_doc}
    )
    
    return {
        "success": True,
        "message": "MSA template updated successfully",
    }


@hr_router.delete("/templates/{template_id}")
async def delete_msa_template(
    template_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin", "superadmin", "accountant"])),
):
    """Delete an MSA template."""
    db = await get_db()
    
    try:
        existing = await db.msa_templates.find_one({"_id": ObjectId(template_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permission
    if current_user["role"] not in ["admin", "superadmin"]:
        if existing["created_by"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    await db.msa_templates.delete_one({"_id": ObjectId(template_id)})
    
    return {
        "success": True,
        "message": "MSA template deleted successfully",
    }

