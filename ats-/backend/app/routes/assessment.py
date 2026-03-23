from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.core.config import settings
from app.services.email_service import send_email
import secrets
import hashlib

router = APIRouter(prefix="/api/hr/assessments", tags=["Assessments"])
public_router = APIRouter(prefix="/api/assessment", tags=["Assessment Public"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SendAssessmentRequest(BaseModel):
    resume_id: str
    jd_id: str
    candidate_name: str
    candidate_email: EmailStr
    jd_title: str
    custom_message: Optional[str] = None
    duration_hours: Optional[int] = 0
    duration_minutes: Optional[int] = 0


class AssessmentSubmitRequest(BaseModel):
    full_name: str
    responses: Dict[str, Any]
    additional_notes: Optional[str] = None


# ─── HR Routes ────────────────────────────────────────────────────────────────

@router.post("/send")
async def send_assessment(
    body: SendAssessmentRequest,
    db=Depends(get_db),
    current_user=Depends(require_roles(["hr", "admin"]))
):
    """Send assessment link to candidate via email"""
    
    # Generate unique token
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    
    total_minutes = (body.duration_hours or 0) * 60 + (body.duration_minutes or 0)
    if total_minutes <= 0:
        total_minutes = 7 * 24 * 60  # default 7 days if nothing selected
    expires_at = None  # Link never expires — timer starts only when candidate clicks Start

    # Save assessment record
    assessment_doc = {
        "resume_id": body.resume_id,
        "jd_id": body.jd_id,
        "candidate_name": body.candidate_name,
        "candidate_email": body.candidate_email,
        "jd_title": body.jd_title,
        "token_hash": token_hash,
        "status": "pending",
        "sent_by": str(current_user["_id"]),
        "sent_by_name": current_user.get("full_name") or current_user.get("username", "HR Team"),
        "sent_at": datetime.now(timezone.utc),
        "expires_at": None,
        "assessment_duration_seconds": total_minutes * 60,  # Store duration, not expiry
        "candidate_responses": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    result = await db["assessments"].insert_one(assessment_doc)
    assessment_id = str(result.inserted_id)
    
    # Build assessment link
    frontend_url = getattr(settings, "frontend_url", "http://localhost:3000")
    assessment_link = f"{frontend_url}/assessment/{raw_token}"
    
    # Build email HTML
    custom_msg = body.custom_message or ""

    hours_display = body.duration_hours or 0
    minutes_display = body.duration_minutes or 0
    if hours_display == 0 and minutes_display == 0:
        time_display = "7 days"
    elif hours_display > 0 and minutes_display > 0:
        time_display = f"{hours_display} hour(s) and {minutes_display} minute(s)"
    elif hours_display > 0:
        time_display = f"{hours_display} hour(s)"
    else:
        time_display = f"{minutes_display} minute(s)"

    email_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">SynHireOne</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0;">AI-Powered Hiring Platform</p>
        </div>
        <div style="background: #ffffff; padding: 32px; border: 1px solid #e5e7eb; border-top: none;">
            <p style="color: #374151; font-size: 16px;">Dear <strong>{body.candidate_name}</strong>,</p>
            <p style="color: #374151; font-size: 15px; line-height: 1.6;">
                Congratulations! We have reviewed your profile and are pleased to inform you that 
                you have been <strong>shortlisted for the <span style="color: #4f46e5;">{body.jd_title}</span> role</strong>.
            </p>
            <p style="color: #374151; font-size: 15px; line-height: 1.6;">
                As the next step in our hiring process, we invite you to complete a short online assessment. 
                This will help us better understand your skills and suitability for the role.
            </p>
            {f'<p style="color: #374151; font-size: 15px; line-height: 1.6; background: #f3f4f6; padding: 12px; border-radius: 8px; border-left: 4px solid #4f46e5;">{custom_msg}</p>' if custom_msg else ""}
            <div style="text-align: center; margin: 32px 0;">
                <a href="{assessment_link}" 
                   style="background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 14px 32px; 
                          border-radius: 8px; text-decoration: none; font-size: 16px; font-weight: bold;
                          display: inline-block;">
                    Start Assessment →
                </a>
            </div>
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <p style="color: #1e40af; margin: 0; font-size: 14px;">
                    📋 <strong>Note:</strong> Complete the assessment at your convenience. 
                </p>
            </div>
            <p style="color: #6b7280; font-size: 14px;">
                If you have any questions, please reply to this email or contact our HR team.
            </p>
            <p style="color: #374151; font-size: 15px;">
                Best regards,<br/>
                <strong>{assessment_doc['sent_by_name']}</strong><br/>
                HR Team, SynHireOne
            </p>
        </div>
        <div style="background: #f9fafb; padding: 16px; border-radius: 0 0 12px 12px; text-align: center; border: 1px solid #e5e7eb; border-top: none;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">This email was sent via SynHireOne. Do not share this link with others.</p>
        </div>
    </div>
    """
    
    # Send email
    await send_email(
        to_email=body.candidate_email,
        subject=f"Assessment Invitation – {body.jd_title} Role | SynHireOne",
        body=email_html,
        is_html=True,
        from_name=assessment_doc["sent_by_name"]
    )
    
    return {
        "message": "Assessment email sent successfully",
        "assessment_id": assessment_id,
        "candidate_email": body.candidate_email,
    }


@router.get("/list")
async def list_assessments(
    db=Depends(get_db),
    current_user=Depends(require_roles(["hr", "admin"]))
):
    """List all assessments sent by this HR/admin"""
    query = {}
    if current_user.get("role") == "hr":
        query["sent_by"] = str(current_user["_id"])
    
    cursor = db["assessments"].find(query).sort("created_at", -1)
    assessments = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        doc.pop("token_hash", None)  # never expose token hash
        assessments.append(doc)
    
    return assessments


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    db=Depends(get_db),
    current_user=Depends(require_roles(["hr", "admin"]))
):
    """Get single assessment details"""
    doc = await db["assessments"].find_one({"_id": ObjectId(assessment_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    doc.pop("token_hash", None)
    return doc


# ─── Public Routes (no auth needed) ──────────────────────────────────────────

@public_router.get("/{token}")
async def get_assessment_public(token: str, db=Depends(get_db)):
    """Get assessment by token (public - for candidate)"""
    token_hash = _hash_token(token)
    doc = await db["assessments"].find_one({"token_hash": token_hash})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment link is invalid or has expired.")
    
    if doc.get("status") == "completed":
        raise HTTPException(status_code=400, detail="This assessment has already been completed.")
    
    duration_seconds = doc.get("assessment_duration_seconds", 0)
    
    return {
        "candidate_name": doc["candidate_name"],
        "candidate_email": doc["candidate_email"],
        "jd_title": doc["jd_title"],
        "sent_by_name": doc.get("sent_by_name", "HR Team"),
        "assessment_duration_seconds": duration_seconds,
        "time_remaining_seconds": duration_seconds,
    }


@public_router.post("/{token}/submit")
async def submit_assessment(
    token: str,
    body: AssessmentSubmitRequest,
    db=Depends(get_db)
):
    """Submit assessment responses (public - for candidate)"""
    token_hash = _hash_token(token)
    doc = await db["assessments"].find_one({"token_hash": token_hash})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment link is invalid.")
    if doc.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Assessment already submitted.")
    
    # Save responses
    await db["assessments"].update_one(
        {"token_hash": token_hash},
        {"$set": {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc),
            "candidate_responses": {
                "full_name": body.full_name,
                "responses": body.responses,
                "additional_notes": body.additional_notes,
            },
            "updated_at": datetime.now(timezone.utc),
        }}
    )
    
    return {"message": "Assessment submitted successfully. Thank you!"}
