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
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.core.config import settings
from app.services.email_service import send_offer_letter_email, send_email_with_attachment
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


hr_router = APIRouter(prefix="/api/hr/offer-signatures", tags=["Offer Signatures"])
public_router = APIRouter(prefix="/api/offer-signatures", tags=["Offer Signatures Public"])


class OfferSignatureListItem(BaseModel):
    id: str
    candidate_name: str
    candidate_email: EmailStr
    company_name: str
    hr_name: str
    hr_email: EmailStr
    position_title: Optional[str]
    status: str
    created_at: datetime
    signed_at: Optional[datetime]
    signed_by_name: Optional[str]
    signed_pdf_url: Optional[str]


class OfferSignaturePublicResponse(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    company_name: str
    hr_name: str
    hr_email: EmailStr
    position_title: Optional[str]
    offer_html: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _strip_html(raw_html: str) -> List[str]:
    # Basic cleanup for PDF generation - remove tags and keep line breaks
    # Replace common HTML tags with newlines to preserve structure
    html = raw_html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    html = html.replace("</p>", "\n").replace("</div>", "\n")
    html = html.replace("</h1>", "\n").replace("</h2>", "\n").replace("</h3>", "\n")
    html = html.replace("</h4>", "\n").replace("</h5>", "\n").replace("</h6>", "\n")
    html = html.replace("</li>", "\n")
    
    # Remove all HTML tags
    text = re.sub(r"<[^>]+>", "", html)
    
    # Decode HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    
    # Split into lines and clean up
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) > 1:  # Skip empty lines and single characters
            lines.append(line)
    
    return lines


def _build_structured_sections(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Convert plain lines into structured sections so labels and values stay together.

    Returns list of dicts with type:
      - {"type": "heading", "text": ...}
      - {"type": "paragraph", "text": ...}
      - {"type": "row", "label": ..., "value": ...}
    """

    sections: List[Dict[str, Any]] = []
    headings = {
        "position summary",
        "position details",
        "benefits & perks",
        "next steps",
        "contact information",
        "hr authorization",
        "candidate digital acceptance",
        "notes",
        "1. documentation",
        "2. duties and work hours",
        "3. compensation",
        "4. termination, notice, and conduct obligations",
        "5. confidentiality, non-disclosure & intellectual property protection",
        "6. breach of agreement & legal consequences",
        "7. transfer, assignment & reposting policy",
        "8. annexure a: compensation structure",
        "9. signature page",
        "documentation",
        "duties and work hours",
        "compensation",
        "termination, notice, and conduct obligations",
        "confidentiality, non-disclosure & intellectual property protection",
        "breach of agreement & legal consequences",
        "transfer, assignment & reposting policy",
        "annexure a: compensation structure",
        "signature page",
    }

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        lowered = line.lower()
        
        # Check if it's a known heading
        is_heading = lowered in headings
        
        # Also check if line starts with a number (like "1. Documentation")
        if not is_heading and re.match(r'^\d+\.', line):
            is_heading = True
        
        # Check if it's a short line that looks like a heading (uppercase, no period at end)
        if not is_heading and len(line) < 100 and line[0].isupper() and not line.endswith('.'):
            # Check if next line doesn't start with lowercase (which would indicate continuation)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line[0].islower():
                    is_heading = True
            else:
                is_heading = True
        
        if is_heading:
            sections.append({"type": "heading", "text": line})
            i += 1
            continue

        # Check for label:value pairs
        if ":" in line and len(line) < 200:
            # Try to split at the first colon
            parts = line.split(":", 1)
            if len(parts) == 2:
                label = parts[0].strip()
                value = parts[1].strip()
                
                # If label is short and value exists, treat as row
                if len(label) < 60 and value:
                    sections.append({"type": "row", "label": label, "value": value})
                    i += 1
                    continue
        
        # Check if line ends with colon (label without value on same line)
        if line.endswith(":"):
            label = line[:-1].strip()
            value_parts: List[str] = []
            j = i + 1
            while j < len(lines):
                candidate = lines[j].strip()
                if not candidate:
                    j += 1
                    continue
                # Stop if we hit another label or heading
                if candidate.endswith(":") or candidate.lower() in headings or re.match(r'^\d+\.', candidate):
                    break
                value_parts.append(candidate)
                j += 1
                # Only collect a few lines for the value
                if len(value_parts) >= 5:
                    break
            
            if value_parts:
                value = " ".join(value_parts).strip()
                sections.append({"type": "row", "label": label, "value": value})
                i = j
                continue
            else:
                # Label with no value, treat as heading
                sections.append({"type": "heading", "text": label})
                i += 1
                continue

        # Default: treat as paragraph
        sections.append({"type": "paragraph", "text": line})
        i += 1

    return sections


def _remove_signature_sections(html: str) -> str:
    """Remove signature-related sections from HTML template."""
    # Remove common signature section patterns
    patterns = [
        r'<[^>]*>Signature\s+of\s+Employee:.*?</[^>]*>',
        r'Signature\s+of\s+Employee:.*?(?=<|$)',
        r'<[^>]*>Name:\s*[^<]*</[^>]*>',
        r'Name:\s+[^\n<]+',
        r'<[^>]*>Date:\s*[^<]*</[^>]*>',
        r'Date:\s+[^\n<]+',
        r'<[^>]*>For\s+and\s+on\s+behalf\s+of.*?</[^>]*>',
        r'For\s+and\s+on\s+behalf\s+of[^\n<]+',
        r'<[^>]*>Sincerely,?</[^>]*>',
        r'Sincerely,?\s*',
        r'<[^>]*>Operations\s+Manager</[^>]*>',
        r'Operations\s+Manager',
        r'<[^>]*>HR\s+Authorization</[^>]*>',
        r'HR\s+Authorization',
        r'<[^>]*>Candidate\s+Digital\s+Acceptance</[^>]*>',
        r'Candidate\s+Digital\s+Acceptance',
        r'<[^>]*>Authorized\s+Signature:?</[^>]*>',
        r'Authorized\s+Signature:?',
        r'<[^>]*>Candidate\s+Signature:?</[^>]*>',
        r'Candidate\s+Signature:?',
        r'<[^>]*>Company\s+Stamp:?</[^>]*>',
        r'Company\s+Stamp:?',
        r'<[^>]*>Accepted\s+by</[^>]*>',
        r'Accepted\s+by',
        r'<[^>]*>Accepted\s+on</[^>]*>',
        r'Accepted\s+on',
        r'_+\s*(?=<|Name:|Date:|$)',  # Remove underscores
    ]
    
    cleaned_html = html
    for pattern in patterns:
        cleaned_html = re.sub(pattern, '', cleaned_html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    # Remove "9. Signature Page" section if it exists
    cleaned_html = re.sub(r'9\.\s*Signature\s+Page.*?(?=\d+\.|$)', '', cleaned_html, flags=re.IGNORECASE | re.DOTALL)
    
    return cleaned_html


def _generate_signed_pdf(
    offer_html: str,
    candidate_name: str,
    acknowledged_name: str,
    signature_path: Optional[str],
    stamp_path: Optional[str],
    hr_signature_path: Optional[str] = None,
    hr_stamp_path: Optional[str] = None,
    company_name: Optional[str] = None,
    hr_name: Optional[str] = None,
    hr_email: Optional[str] = None,
) -> (str, bytes):
    # Clean the HTML to remove signature sections
    offer_html = _remove_signature_sections(offer_html)
    
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.close()

    doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#1D4ED8")
    accent_color = colors.HexColor("#F3F4F6")
    text_color = colors.HexColor("#1F2937")

    title_style = ParagraphStyle(
        "OfferTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=primary_color,
        alignment=0,
        spaceAfter=12,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=text_color,
        fontSize=14,
        spaceBefore=18,
        spaceAfter=8,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#4B5563"),
        fontSize=11,
        leading=16,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["BodyText"],
        textColor=text_color,
        fontSize=11,
        leading=16,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        textColor=text_color,
        fontSize=11,
        leading=16,
    )

    story: List[Any] = []

    # Decorative header
    header_text = company_name or "Offer Letter"
    header_table = Table(
        [[Paragraph(f"<b>{header_text}</b>", ParagraphStyle("Header", parent=styles["Heading1"], textColor=colors.white, fontSize=16))]],
        colWidths=[doc.width],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), primary_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 18))

    story.append(Paragraph(f"Offer Letter Acceptance - {candidate_name}", title_style))

    if hr_name or hr_email:
        info_rows: List[List[Paragraph]] = []
        if hr_name:
            info_rows.append([Paragraph("<b>HR Contact</b>", label_style), Paragraph(hr_name, value_style)])
        if hr_email:
            info_rows.append([Paragraph("<b>HR Email</b>", label_style), Paragraph(hr_email, value_style)])

        if info_rows:
            info_table = Table(info_rows, colWidths=[doc.width * 0.3, doc.width * 0.7])
            info_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), accent_color),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 12),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(info_table)
            story.append(Spacer(1, 18))

    lines = _strip_html(offer_html)
    structured = _build_structured_sections(lines)

    for entry in structured:
        if entry["type"] == "heading":
            story.append(Paragraph(entry["text"], section_heading))
        elif entry["type"] == "row":
            value_text = entry.get("value") or "—"
            label_text = entry.get("label", "")

            is_long = (
                len(label_text) > 60
                or len(value_text) > 180
                or value_text.count("•") > 0
                or value_text.count(" a)") > 0
                or "\n" in value_text
            )

            if is_long:
                story.append(Paragraph(f"<b>{label_text}</b>", label_style))
                if value_text and value_text != "—":
                    story.append(Paragraph(value_text, body_style))
            else:
                row_table = Table(
                    [
                        [
                            Paragraph(f"<b>{label_text}</b>", label_style),
                            Paragraph(value_text, value_style),
                        ]
                    ]
                    ,
                    colWidths=[doc.width * 0.28, doc.width * 0.72],
                )
                row_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(row_table)
        else:  # paragraph
            story.append(Paragraph(entry["text"], body_style))
        story.append(Spacer(1, 6))

    # Add space before signatures
    story.append(Spacer(1, 24))
    
    # HR authorization block (if provided) - Simple format
    if hr_signature_path or hr_stamp_path:
        if hr_signature_path:
            try:
                hr_signature_img = Image(hr_signature_path, width=2.2 * inch, height=0.9 * inch)
                hr_signature_img.hAlign = "LEFT"
                story.append(hr_signature_img)
                story.append(Spacer(1, 8))
            except Exception:
                pass
        
        story.append(Paragraph(f"{hr_name or 'HR Manager'}", body_style))
        story.append(Paragraph(company_name or "", body_style))
        
        if hr_stamp_path:
            try:
                hr_stamp_img = Image(hr_stamp_path, width=1.3 * inch, height=1.3 * inch)
                hr_stamp_img.hAlign = "LEFT"
                story.append(Spacer(1, 8))
                story.append(hr_stamp_img)
            except Exception:
                pass
        
        story.append(Spacer(1, 24))

    # Candidate acceptance section - Simple format
    if signature_path:
        try:
            candidate_signature_img = Image(signature_path, width=2.2 * inch, height=0.9 * inch)
            candidate_signature_img.hAlign = "LEFT"
            story.append(candidate_signature_img)
            story.append(Spacer(1, 8))
        except Exception:
            pass
    
    story.append(Paragraph(acknowledged_name, body_style))
    story.append(Paragraph(datetime.now(timezone.utc).strftime('%Y-%m-%d'), body_style))
    
    # Add stamp if provided
    if stamp_path:
        try:
            candidate_stamp_img = Image(stamp_path, width=1.3 * inch, height=1.3 * inch)
            candidate_stamp_img.hAlign = "LEFT"
            story.append(Spacer(1, 8))
            story.append(candidate_stamp_img)
        except Exception:
            pass

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

    suffix = ""
    if upload.filename:
        _, ext = os.path.splitext(upload.filename)
        suffix = ext

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    contents = await upload.read()
    temp_file.write(contents)
    temp_file.close()
    await upload.seek(0)
    return temp_file.name


@hr_router.post("/initiate", response_model=Dict[str, Any])
async def initiate_offer_signature(
    candidate_email: EmailStr = Form(...),
    candidate_name: str = Form(...),
    offer_html: str = Form(...),
    company_name: str = Form(...),
    hr_name: str = Form(...),
    hr_email: EmailStr = Form(...),
    position_title: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    enable_esign: Optional[str] = Form("true"),
    expires_in_days: Optional[int] = Form(7),
    hr_signature: UploadFile = File(None),
    hr_stamp: UploadFile = File(None),
    current_user: dict = Depends(require_roles(["hr", "admin"])),
):
    enable_esign_bool = str(enable_esign).lower() in ("1", "true", "yes", "on")

    if not enable_esign_bool:
        # Fallback to simple email send without e-signature flow
        await send_offer_letter_email(
            to_email=candidate_email,
            candidate_name=candidate_name,
            offer_details=offer_html,
            hr_name=hr_name,
            hr_email=hr_email,
            company_name=company_name,
            subject=subject or f"Offer Letter - {company_name}",
            is_html=True,
        )
        return {
            "message": "Offer letter sent without e-signature workflow",
            "esign_enabled": False,
        }

    db = await get_db()
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_days = int(expires_in_days or 7)

    hr_signature_temp = await _save_upload_to_temp(hr_signature) if hr_signature else None
    hr_stamp_temp = await _save_upload_to_temp(hr_stamp) if hr_stamp else None

    hr_signature_url = None
    hr_signature_filename = None
    if hr_signature_temp and hr_signature:
        hr_signature_url = await storage_service.save_file(
            hr_signature_temp, f"offer_signatures/hr/signatures/{hr_signature.filename or 'hr-signature.png'}"
        )
        if hr_signature_url and "/uploads/" in hr_signature_url:
            hr_signature_filename = hr_signature_url.split("/uploads/")[1]
        else:
            hr_signature_filename = hr_signature_url

    hr_stamp_url = None
    hr_stamp_filename = None
    if hr_stamp_temp and hr_stamp:
        hr_stamp_url = await storage_service.save_file(
            hr_stamp_temp, f"offer_signatures/hr/stamps/{hr_stamp.filename or 'hr-stamp.png'}"
        )
        if hr_stamp_url and "/uploads/" in hr_stamp_url:
            hr_stamp_filename = hr_stamp_url.split("/uploads/")[1]
        else:
            hr_stamp_filename = hr_stamp_url

    for temp_file in [hr_signature_temp, hr_stamp_temp]:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

    doc = {
        "candidate_email": candidate_email,
        "candidate_name": candidate_name,
        "company_name": company_name,
        "hr_name": hr_name,
        "hr_email": hr_email,
        "position_title": position_title,
        "offer_html": offer_html,
        "status": "pending",
        "candidate_position": position_title,
        "signature_token_hash": token_hash,
        "token_expires_at": now + timedelta(days=expires_days),
        "created_at": now,
        "updated_at": now,
        "hr_user_id": str(current_user["_id"]),
        "signed_at": None,
        "signed_by_name": None,
        "signed_pdf_url": None,
        "hr_signature_url": hr_signature_url,
        "hr_signature_filename": hr_signature_filename,
        "hr_stamp_url": hr_stamp_url,
        "hr_stamp_filename": hr_stamp_filename,
    }

    result = await db.offer_signatures.insert_one(doc)
    record_id = str(result.inserted_id)

    signature_link = f"{settings.frontend_base_url.rstrip('/')}/offer-sign/{token}"
    offer_with_cta = f"""{offer_html}
<div style="margin-top:24px;padding:20px;background:#f5f5f5;border-radius:10px;text-align:center;">
  <h3 style="margin-bottom:12px;color:#2563EB;">Ready to accept your offer?</h3>
  <p style="margin-bottom:20px;font-size:14px;color:#4B5563;">
    Click the button below to review and digitally sign your offer letter.<br/>
    You can upload your signature and optional company stamp before submitting.
  </p>
  <a href="{signature_link}" style="display:inline-block;background:#2563EB;color:#ffffff;padding:12px 24px;border-radius:999px;text-decoration:none;font-weight:600;">
    View &amp; Sign Offer Letter
  </a>
</div>
<p style="font-size:12px;color:#6B7280;margin-top:16px;">If the button above does not work, copy and paste this link into your browser:<br/>{signature_link}</p>
"""

    await send_offer_letter_email(
        to_email=candidate_email,
        candidate_name=candidate_name,
        offer_details=offer_with_cta,
        hr_name=hr_name,
        hr_email=hr_email,
        company_name=company_name,
        subject=subject or f"Offer Letter - {company_name}",
        is_html=True,
    )

    return {
        "message": "Offer letter with e-signature link sent successfully",
        "esign_enabled": True,
        "signature_link": signature_link,
        "record_id": record_id,
    }


@hr_router.get("/", response_model=List[OfferSignatureListItem])
async def list_offer_signatures(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
):
    db = await get_db()
    query: Dict[str, Any] = {"hr_user_id": str(current_user["_id"])}
    if current_user["role"] == "admin":
        # Admins can see all signatures
        query = {}
    if status_filter:
        query["status"] = status_filter

    records = await db.offer_signatures.find(query).sort("created_at", -1).to_list(None)

    items: List[OfferSignatureListItem] = []
    for record in records:
        items.append(
            OfferSignatureListItem(
                id=str(record["_id"]),
                candidate_name=record.get("candidate_name"),
                candidate_email=record.get("candidate_email"),
                company_name=record.get("company_name"),
                hr_name=record.get("hr_name"),
                hr_email=record.get("hr_email"),
                position_title=record.get("position_title"),
                status=record.get("status"),
                created_at=record.get("created_at"),
                signed_at=record.get("signed_at"),
                signed_by_name=record.get("signed_by_name"),
                signed_pdf_url=record.get("signed_pdf_url"),
            )
        )

    return items


@public_router.get("/{token}", response_model=OfferSignaturePublicResponse)
async def get_offer_signature(token: str):
    db = await get_db()
    token_hash = _hash_token(token)

    record = await db.offer_signatures.find_one({"signature_token_hash": token_hash})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer letter not found")

    if record.get("status") == "signed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Offer letter already signed")

    expires_at = _normalize_datetime(record.get("token_expires_at"))
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Offer letter link has expired",
        )

    raw_html = record.get("offer_html", "") or ""
    cleaned_html = re.sub(r"</?body[^>]*>", "", raw_html, flags=re.IGNORECASE)
    cleaned_html = re.sub(r"\s*\(Consolidated\s+CTC\)", "", cleaned_html, flags=re.IGNORECASE)

    return OfferSignaturePublicResponse(
        candidate_name=record.get("candidate_name"),
        candidate_email=record.get("candidate_email"),
        company_name=record.get("company_name"),
        hr_name=record.get("hr_name"),
        hr_email=record.get("hr_email"),
        position_title=record.get("position_title"),
        offer_html=cleaned_html,
    )


@public_router.post("/{token}/complete")
async def complete_offer_signature(
    token: str,
    full_name: str = Form(...),
    signature: UploadFile = File(...),
    company_stamp: Optional[UploadFile] = File(None),
):
    db = await get_db()
    token_hash = _hash_token(token)

    record = await db.offer_signatures.find_one({"signature_token_hash": token_hash})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer letter not found")

    if record.get("status") == "signed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Offer letter already signed")

    expires_at = _normalize_datetime(record.get("token_expires_at"))
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Offer letter link has expired",
        )

    signature_temp_path = await _save_upload_to_temp(signature)
    stamp_temp_path = await _save_upload_to_temp(company_stamp) if company_stamp else None

    # Upload signature and stamp to storage
    signature_url = None
    candidate_signature_filename = None
    stamp_url = None
    candidate_stamp_filename = None
    if signature_temp_path:
        signature_url = await storage_service.save_file(
            signature_temp_path, f"offer_signatures/signatures/{signature.filename or 'signature.png'}"
        )
        if signature_url and "/uploads/" in signature_url:
            candidate_signature_filename = signature_url.split("/uploads/")[1]
        else:
            candidate_signature_filename = signature_url
    if stamp_temp_path:
        stamp_url = await storage_service.save_file(
            stamp_temp_path, f"offer_signatures/stamps/{company_stamp.filename or 'stamp.png'}"
        )
        if stamp_url and "/uploads/" in stamp_url:
            candidate_stamp_filename = stamp_url.split("/uploads/")[1]
        else:
            candidate_stamp_filename = stamp_url

    hr_signature_local = _local_path_from_filename(record.get("hr_signature_filename"))
    hr_stamp_local = _local_path_from_filename(record.get("hr_stamp_filename"))

    original_offer_html = record.get("offer_html", "") or ""
    cleaned_offer_html = re.sub(r"</?body[^>]*>", "", original_offer_html, flags=re.IGNORECASE)
    cleaned_offer_html = re.sub(r"\s*\(Consolidated\s+CTC\)", "", cleaned_offer_html, flags=re.IGNORECASE)

    pdf_path, pdf_bytes = _generate_signed_pdf(
        offer_html=cleaned_offer_html,
        candidate_name=record.get("candidate_name", ""),
        acknowledged_name=full_name,
        signature_path=signature_temp_path,
        stamp_path=stamp_temp_path,
        hr_signature_path=hr_signature_local,
        hr_stamp_path=hr_stamp_local,
        company_name=record.get("company_name"),
        hr_name=record.get("hr_name"),
        hr_email=record.get("hr_email"),
    )

    pdf_url = await storage_service.save_file(pdf_path, f"offer_signatures/final/{record.get('_id')}.pdf")

    # Clean up temp files
    for path in [signature_temp_path, stamp_temp_path, pdf_path]:
        if path and os.path.exists(path):
            os.remove(path)

    now = datetime.now(timezone.utc)
    await db.offer_signatures.update_one(
        {"_id": record["_id"]},
        {
            "$set": {
                "status": "signed",
                "signed_at": now,
                "signed_by_name": full_name,
                "signed_pdf_url": pdf_url,
                "signature_image_url": signature_url,
                "stamp_image_url": stamp_url,
                "candidate_signature_filename": candidate_signature_filename,
                "candidate_stamp_filename": candidate_stamp_filename,
                "updated_at": now,
            }
        },
    )

    # Send confirmation emails with attachment
    subject = f"Signed Offer Letter - {record.get('company_name', '')}"
    body = f"""
<p>Hi {record.get('candidate_name')},</p>
<p>Thank you for signing your offer letter. A copy of the signed document is attached for your records.</p>
<p>Best regards,<br/>{record.get('hr_name')}</p>
"""

    await send_email_with_attachment(
        to_email=record.get("candidate_email"),
        subject=subject,
        body=body,
        is_html=True,
        from_name=record.get("hr_name"),
        from_email=record.get("hr_email"),
        attach_pdf=pdf_bytes,
        pdf_filename=f"signed-offer-{record.get('candidate_name','candidate')}.pdf",
    )

    hr_body = f"""
<p>Hi {record.get('hr_name')},</p>
<p>The candidate <strong>{record.get('candidate_name')}</strong> has signed the offer letter. The signed copy is attached.</p>
"""

    await send_email_with_attachment(
        to_email=record.get("hr_email"),
        subject=f"Signed Offer Letter Received - {record.get('candidate_name')}",
        body=hr_body,
        is_html=True,
        attach_pdf=pdf_bytes,
        pdf_filename=f"signed-offer-{record.get('candidate_name','candidate')}.pdf",
    )

    return {
        "message": "Offer letter signed successfully",
        "signed_pdf_url": pdf_url,
    }


def include_offer_signature_routes(app):
    app.include_router(hr_router)
    app.include_router(public_router)


                            