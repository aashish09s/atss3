from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, Response, StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
import os
import json
from pydantic import BaseModel, EmailStr
import aiohttp
import io

from app.core.config import settings
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.services.storage import StorageService
from app.services.ai_service import score_resume_against_jd
from app.services.email_service import send_interview_email, send_offer_letter_email
from app.services.whatsapp_service import whatsapp_service
from app.routes.websocket import notify_resume_update

router = APIRouter(prefix="/api/hr/resume", tags=["Resume Actions"])


class ShareResumeRequest(BaseModel):
    resume_id: str
    manager_id: Optional[str] = None  # Optional explicit target manager for admins or HR without link


class UpdateStatusRequest(BaseModel):
    status: str  # submission, shortlisting, interview, reject, select, offer_letter, onboarding


class SendInterviewRequest(BaseModel):
    candidate_email: EmailStr
    interview_date: Optional[str] = None
    interview_time: Optional[str] = None
    message: Optional[str] = None


class SendInterviewEmailRequest(BaseModel):
    resume_id: str
    candidate_email: str
    candidate_name: str
    position: Optional[str] = ""  # Position field (optional)
    subject: str
    email_body: str
    virtual_interview_link: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_name: str
    hr_name: str
    hr_email: str


class GenerateOfferRequest(BaseModel):
    candidate_name: str
    position: str
    salary: Optional[str] = None
    start_date: Optional[str] = None


class SendOfferLetterRequest(BaseModel):
    to_email: str
    candidate_name: str
    position: Optional[str] = ""  # Position field (optional)
    subject: str
    email_body: str
    is_html: bool = True
    company_name: str
    hr_name: str
    hr_email: str


class ShareWithClientRequest(BaseModel):
    resume_id: str
    to_emails: str  # Comma-separated email addresses
    cc_emails: Optional[str] = None
    bcc_emails: Optional[str] = None
    subject: str
    email_body: str
    resume_attachment: bool = True
    candidate_name: str
    candidate_position: str
    company_name: str
    hr_name: str
    hr_email: str
    status_options: Optional[dict] = None


class ShareWithClientWhatsAppRequest(BaseModel):
    resume_id: str
    to_phones: str  # Comma-separated phone numbers
    candidate_name: str
    candidate_position: str
    company_name: str
    hr_name: str
    hr_phone: str
    additional_message: Optional[str] = None
    resume_url: Optional[str] = None


@router.post("/share")
async def share_resume_with_manager(
    share_data: ShareResumeRequest,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Share resume with linked manager"""
    db = await get_db()
    
    # Determine target manager
    target_manager_id: Optional[str] = None
    if current_user.get("manager_id"):
        target_manager_id = current_user.get("manager_id")
    elif share_data.manager_id:
        target_manager_id = share_data.manager_id
    
    # If still missing, try to fallback to any existing manager (admin convenience)
    if not target_manager_id:
        try:
            db = await get_db()
            any_manager = await db.users.find_one({"role": "manager"})
            if any_manager:
                target_manager_id = str(any_manager["_id"])
        except Exception:
            pass
    # If still missing, fail with clear error
    if not target_manager_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No manager specified or linked. Provide 'manager_id' or link a manager to your account."
        )
    
    try:
        resume_object_id = ObjectId(share_data.resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID"
        )
    
    # Get resume
    resume_query = {"_id": resume_object_id}
    if current_user["role"] != "admin":
        resume_query["uploaded_by"] = str(current_user["_id"])

    resume = await db.resumes.find_one(resume_query)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Update resume to mark as shared
    await db.resumes.update_one(
        {"_id": resume_object_id},
        {
            "$set": {
                "shared_with_manager": True,
                "shared_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Notify manager via WebSocket
    try:
        await notify_resume_update(
            share_data.resume_id,
            "shared",
            str(current_user["_id"]),
            target_manager_id
        )
    except Exception as e:
        print(f"WebSocket notification error: {str(e)}")
    
    return {"message": "Resume shared with manager successfully"}


@router.patch("/status")
async def update_resume_status(
    status_data: UpdateStatusRequest,
    resume_id: str,
    current_user: dict = Depends(require_roles(["hr", "manager"]))
):
    """Update resume status"""
    db = await get_db()
    
    try:
        resume_object_id = ObjectId(resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID"
        )
    
    # Different access rules for HR vs Manager
    if current_user["role"] == "hr":
        # HR can update their own resumes
        resume = await db.resumes.find_one({
            "_id": resume_object_id,
            "uploaded_by": str(current_user["_id"])
        })
    else:  # manager
        # Manager can update resumes shared with them
        # First get HR users linked to this manager
        hr_users = await db.users.find({
            "manager_id": str(current_user["_id"]),
            "role": "hr"
        }).to_list(None)
        
        hr_user_ids = [str(hr["_id"]) for hr in hr_users]
        
        resume = await db.resumes.find_one({
            "_id": resume_object_id,
            "uploaded_by": {"$in": hr_user_ids},
            "shared_with_manager": True
        })
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Valid status options
    valid_statuses = [
        "submission", "shortlisting", "interview", 
        "reject", "select", "offer_letter", "onboarding"
    ]
    
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid options: {', '.join(valid_statuses)}"
        )
    
    # Update status
    await db.resumes.update_one(
        {"_id": resume_object_id},
        {
            "$set": {
                "status": status_data.status,
                "status_updated_by": str(current_user["_id"]),
                "status_updated_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Notify relevant users via WebSocket
    try:
        if current_user["role"] == "hr":
            # Notify linked manager
            await notify_resume_update(
                resume_id,
                "status_changed",
                str(current_user["_id"]),
                current_user.get("manager_id")
            )
        else:  # manager
            # Notify HR who uploaded the resume
            await notify_resume_update(
                resume_id,
                "status_changed",
                resume["uploaded_by"],
                str(current_user["_id"])
            )
    except Exception as e:
        print(f"WebSocket notification error: {str(e)}")
    
    return {"message": "Resume status updated successfully"}


@router.get("/download/{resume_id}")
async def download_resume(
    resume_id: str,
    current_user: dict = Depends(require_roles(["hr", "manager", "admin"]))
):
    """Download resume file"""
    db = await get_db()
    
    try:
        resume_object_id = ObjectId(resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID"
        )
    
    # Access control logic - Admins can see all resumes
    if current_user["role"] == "admin":
        resume = await db.resumes.find_one({
            "_id": resume_object_id
        })
    elif current_user["role"] == "hr":
        resume = await db.resumes.find_one({
            "_id": resume_object_id,
            "uploaded_by": str(current_user["_id"])
        })
    else:  # manager
        hr_users = await db.users.find({
            "manager_id": str(current_user["_id"]),
            "role": "hr"
        }).to_list(None)
        
        hr_user_ids = [str(hr["_id"]) for hr in hr_users]
        
        resume = await db.resumes.find_one({
            "_id": resume_object_id,
            "uploaded_by": {"$in": hr_user_ids},
            "shared_with_manager": True
        })
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Handle local vs S3 files
    file_url = resume["file_url"]
    
    if file_url.startswith("/uploads/"):
        # Local file
        filename = file_url.split("/uploads/")[1]
        file_path = os.path.join("uploads", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=resume["filename"],
            media_type='application/octet-stream'
        )
    else:
        # S3/external file - download and serve directly to avoid CORS issues
        try:
            timeout = aiohttp.ClientTimeout(total=60)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(file_url) as response:
                    if response.status != 200:
                        print(f"[DOWNLOAD ERROR] Remote server returned status {response.status} for {file_url}")
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"File not found on remote server (status: {response.status})"
                        )

                    content_type = response.headers.get('Content-Type', 'application/octet-stream')
                    data = await response.read()  # Read entire file into memory (resumes are typically small)

                    filename = resume["filename"]
                    headers = {
                        "Content-Disposition": f'attachment; filename="{filename}"',
                    }

                    content_length = response.headers.get("Content-Length")
                    if content_length and content_length.isdigit():
                        headers["Content-Length"] = content_length
                    else:
                        headers["Content-Length"] = str(len(data))

                    return Response(content=data, media_type=content_type, headers=headers)
        except aiohttp.ClientTimeout:
            print(f"[DOWNLOAD ERROR] Timeout downloading file from {file_url}")
            return Response(status_code=302, headers={"Location": file_url})
        except aiohttp.ClientError as e:
            print(f"[DOWNLOAD ERROR] Network error downloading file from {file_url}: {e}")
            return Response(status_code=302, headers={"Location": file_url})
        except Exception as e:
            print(f"[DOWNLOAD ERROR] Unexpected error downloading file: {e}")
            import traceback
            traceback.print_exc()
            return Response(status_code=302, headers={"Location": file_url})


@router.post("/send-interview")
async def send_interview_email_route(
    interview_data: SendInterviewRequest,
    current_user: dict = Depends(require_roles(["hr", "manager", "admin"]))
):
    """Send interview email to candidate"""
    
    # Prepare interview details
    interview_details = "We are pleased to invite you for an interview.\n\n"
    
    if interview_data.interview_date:
        interview_details += f"Date: {interview_data.interview_date}\n"
    
    if interview_data.interview_time:
        interview_details += f"Time: {interview_data.interview_time}\n"
    
    if interview_data.message:
        interview_details += f"\nAdditional Information:\n{interview_data.message}\n"
    
    interview_details += "\nPlease confirm your availability."
    
    try:
        # Use the new email service with HR user's information
        await send_interview_email(
            to_email=interview_data.candidate_email,
            candidate_name="Candidate",  # You can get this from resume data if needed
            interview_details=interview_details,
            hr_name=current_user.get("name", "HR Team"),
            hr_email=current_user.get("email", "hr@company.com"),
            company_name="SynHireOne"  # You can get this from company settings
        )
        
        return {"message": "Interview email sent successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/send-interview-email")
async def send_interview_email_from_resume(
    email_data: SendInterviewEmailRequest,
    current_user: dict = Depends(require_roles(["hr", "manager", "admin"]))
):
    """Send interview email to candidate using resume data"""
    
    print(f"[DEBUG] Interview email request received")
    print(f"[DEBUG] Email data: {email_data}")
    print(f"[DEBUG] Current user: {current_user}")
    
    try:
        print(f"[DEBUG] Calling send_interview_email service...")
        print(f"[DEBUG] Virtual interview link: {email_data.virtual_interview_link}")
        
        # Enhance email body with virtual interview link if provided
        enhanced_email_body = email_data.email_body
        if email_data.virtual_interview_link:
            enhanced_email_body += f"\n\n**Virtual Interview Link:**\n{email_data.virtual_interview_link}\n\nClick the link above to join the virtual interview."
        
        # Send the email using the new email service
        result = await send_interview_email(
            to_email=email_data.candidate_email,
            candidate_name=email_data.candidate_name,
            interview_details=enhanced_email_body,
            hr_name=email_data.hr_name,
            hr_email=email_data.hr_email,
            company_name=email_data.company_name,
            subject=email_data.subject,
            virtual_interview_link=email_data.virtual_interview_link
        )
        
        print(f"[DEBUG] Email service result: {result}")
        print(f"[SUCCESS] Interview email sent successfully")
        
        return {"message": "Interview email sent successfully"}
        
    except Exception as e:
        error_msg = str(e)
        # Try to encode error message safely for logging
        try:
            print(f"[ERROR] ERROR in interview email endpoint: {error_msg}")
        except UnicodeEncodeError:
            print(f"[ERROR] ERROR in interview email endpoint: {error_msg.encode('ascii', 'ignore').decode('ascii')}")
        
        print(f"[ERROR] ERROR type: {type(e).__name__}")
        import traceback
        try:
            traceback.print_exc()
        except UnicodeEncodeError:
            # Skip traceback if it has encoding issues
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {error_msg}"
        )


@router.post("/generate-offer")
async def generate_offer_letter(
    offer_data: GenerateOfferRequest,
    current_user: dict = Depends(require_roles(["hr", "manager", "admin"]))
):
    """Generate offer letter"""
    
    # Simple offer letter template
    offer_content = f"""
    OFFER LETTER
    
    Dear {offer_data.candidate_name},
    
    We are pleased to offer you the position of {offer_data.position}.
    
    """
    
    if offer_data.salary:
        offer_content += f"Salary: {offer_data.salary}\n"
    
    if offer_data.start_date:
        offer_content += f"Start Date: {offer_data.start_date}\n"
    
    offer_content += """
    
    We look forward to having you join our team.
    
    Best regards,
    HR Team
    """
    
    return {
        "message": "Offer letter generated successfully",
        "offer_content": offer_content
    }


@router.post("/send-offer-letter")
async def send_offer_letter(
    offer_data: SendOfferLetterRequest,
    current_user: dict = Depends(require_roles(["hr", "manager", "admin"]))
):
    """Send offer letter to candidate via email"""
    
    print(f"[DEBUG] Offer letter request received")
    print(f"[DEBUG] Offer data: {offer_data}")
    print(f"[DEBUG] Current user: {current_user}")
    
    try:
        print(f"[DEBUG] Preparing offer details...")
        print(f"[DEBUG] Offer data - email_body length: {len(offer_data.email_body) if offer_data.email_body else 0}")
        print(f"[DEBUG] Offer data - subject: {offer_data.subject}")
        print(f"[DEBUG] Offer data - is_html: {offer_data.is_html}")
        
        # Use the email body directly if it's HTML, otherwise format it
        if offer_data.is_html and offer_data.email_body:
            # Email body is already HTML, use it directly
            offer_details = offer_data.email_body
        else:
            # Format as plain text
            offer_details = f"""
        Position: {offer_data.position}
        Company: {offer_data.company_name}
        
        {offer_data.email_body}
        """
        
        print(f"[DEBUG] Calling send_offer_letter_email service...")
        
        # Use the new email service with HR user's information
        # Use hr_name and hr_email from the request data, not current_user
        result = await send_offer_letter_email(
            to_email=offer_data.to_email,
            candidate_name=offer_data.candidate_name,
            offer_details=offer_details,
            hr_name=offer_data.hr_name,  # Use from request
            hr_email=offer_data.hr_email,  # Use from request
            company_name=offer_data.company_name,  # Use the company name from the form
            subject=offer_data.subject,  # Use the subject from the request
            is_html=offer_data.is_html  # Pass is_html flag
        )
        
        print(f"[DEBUG] Email service result: {result}")
        print(f"[SUCCESS] Offer letter sent successfully")
        
        return {"message": "Offer letter sent successfully"}
        
    except Exception as e:
        print(f"[ERROR] ERROR in offer letter endpoint: {str(e)}")
        print(f"[ERROR] ERROR type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/share-with-client")
async def share_resume_with_client(
    client_data: ShareWithClientRequest,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Share resume with client via email"""
    
    print(f"[DEBUG] Client sharing request received")
    # Safely print client data without emojis
    try:
        print(f"[DEBUG] Resume ID: {client_data.resume_id}")
        print(f"[DEBUG] Resume attachment: {client_data.resume_attachment}")
        print(f"[DEBUG] TO emails: {client_data.to_emails}")
        print(f"[DEBUG] Subject: {client_data.subject[:50] if client_data.subject else 'N/A'}...")
    except Exception as e:
        print(f"[DEBUG] Error printing client data: {str(e)}")
    print(f"[DEBUG] Current user ID: {current_user.get('_id') if current_user else 'None'}")
    
    try:
        # Get resume data from database
        db = await get_db()
        resume = await db.resumes.find_one({"_id": ObjectId(client_data.resume_id)})
        
        print(f"[DEBUG] Resume found in database: {resume is not None}")
        if resume:
            print(f"[DEBUG] Resume filename: {resume.get('filename', 'N/A')}")
            print(f"[DEBUG] Resume file_url: {resume.get('file_url', 'N/A')}")
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Parse email addresses
        to_emails = [email.strip() for email in client_data.to_emails.split(',') if email.strip()]
        cc_emails = [email.strip() for email in client_data.cc_emails.split(',')] if client_data.cc_emails else []
        bcc_emails = [email.strip() for email in client_data.bcc_emails.split(',')] if client_data.bcc_emails else []
        
        # Remove empty strings
        cc_emails = [email for email in cc_emails if email]
        bcc_emails = [email for email in bcc_emails if email]
        
        print(f"[DEBUG] TO emails: {to_emails}")
        print(f"[DEBUG] CC emails: {cc_emails}")
        print(f"[DEBUG] BCC emails: {bcc_emails}")
        
        # Validate email configuration
        from app.core.config import settings
        email_service_available = False
        use_microsoft365 = False
        
        # Try Microsoft 365 first if configured
        if settings.use_microsoft365 and all([settings.microsoft_client_id, settings.microsoft_client_secret, 
                                             settings.microsoft_tenant_id, settings.microsoft_sender_email]):
            try:
                # Test Microsoft 365 service
                from app.services.microsoft365_email_service import Microsoft365EmailService
                ms365_service = Microsoft365EmailService()
                # If we can create the service without error, it's available
                email_service_available = True
                use_microsoft365 = True
                print("[SUCCESS] Microsoft 365 email service configured and available")
            except Exception as e:
                print(f"[ERROR] Microsoft 365 service error: {str(e)}")
                # Fall back to SMTP if available
                if settings.smtp_host and settings.smtp_username and settings.smtp_password:
                    email_service_available = True
                    use_microsoft365 = False
                    print("[SUCCESS] Falling back to SMTP email service")
                else:
                    email_service_available = False
        else:
            # Check if SMTP is configured
            if settings.smtp_host and settings.smtp_username and settings.smtp_password:
                email_service_available = True
                use_microsoft365 = False
                print("[SUCCESS] SMTP email service configured")
        
        if not email_service_available:
            print(f"[ERROR] Email service not configured:")
            print(f"   Use Microsoft 365: {settings.use_microsoft365}")
            print(f"   Microsoft Client ID: {settings.microsoft_client_id}")
            print(f"   Microsoft Tenant ID: {settings.microsoft_tenant_id}")
            print(f"   Microsoft Sender Email: {settings.microsoft_sender_email}")
            print(f"   SMTP Host: {settings.smtp_host}")
            print(f"   SMTP Username: {settings.smtp_username}")
            print(f"   SMTP Password: {'***' if settings.smtp_password else 'None'}")
            
            # For development, return a mock success response
            if settings.environment == "development":
                print("[WARNING] Development mode: Returning mock success response")
                return {
                    "message": "Resume shared with client successfully (MOCK - Email service not configured)",
                    "recipients": {
                        "to": to_emails,
                        "cc": cc_emails,
                        "bcc": bcc_emails
                    },
                    "successful_sends": to_emails + [f"{cc} (CC)" for cc in cc_emails] + [f"{bcc} (BCC)" for bcc in bcc_emails],
                    "failed_sends": [],
                    "mock_response": True
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Email service not configured. Please check SMTP or Microsoft 365 settings in environment variables."
                )
        
        # Send emails to all recipients
        from app.services.email_service import send_email, send_email_with_attachment
        
        # Override the email service decision if we determined it should use Microsoft 365
        if use_microsoft365:
            print("[INFO] Using Microsoft 365 email service")
        else:
            print("[INFO] Using SMTP email service")
        
        # Prepare email content
        email_body = client_data.email_body
        
        # Add company branding if logo is available
        if client_data.company_name:
            # Replace newlines with HTML breaks before using in f-string
            formatted_email_body = email_body.replace('\n', '<br>')
            email_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #2563eb; margin: 0;">{client_data.company_name}</h2>
    </div>
    
    <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        {formatted_email_body}
    </div>
    
    <div style="border-top: 1px solid #e5e7eb; padding-top: 15px; margin-top: 20px;">
        <p style="color: #6b7280; font-size: 14px; margin: 0;">
            Best regards,<br>
            <strong>{client_data.hr_name}</strong><br>
            {client_data.company_name}
        </p>
    </div>
</div>
"""
        
        # Track successful and failed sends
        successful_sends = []
        failed_sends = []
        
        # Update resume status based on selected status options
        if client_data.status_options:
            status_updates = []
            if client_data.status_options.get('resumeSubmission'):
                status_updates.append('submission')
            if client_data.status_options.get('interviewSubmission'):
                status_updates.append('interview')
            if client_data.status_options.get('offerLetterGeneration'):
                status_updates.append('offer_letter')
            if client_data.status_options.get('candidateOnboard'):
                status_updates.append('onboarding')
            
            # Update to the highest priority status
            if status_updates:
                status_priority = {
                    'submission': 1,
                    'interview': 2,
                    'offer_letter': 3,
                    'onboarding': 4
                }
                highest_status = max(status_updates, key=lambda x: status_priority.get(x, 0))
                
                try:
                    await db.resumes.update_one(
                        {"_id": ObjectId(client_data.resume_id)},
                        {
                            "$set": {
                                "status": highest_status,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    print(f"[SUCCESS] Updated resume status to: {highest_status}")
                except Exception as e:
                    print(f"[WARNING] Failed to update resume status: {str(e)}")

        # Send email to primary recipients with PDF attachment
        for to_email in to_emails:
            try:
                print(f"[DEBUG] Sending email to {to_email} with attachment: {client_data.resume_attachment}")
                try:
                    await send_email_with_attachment(
                        to_email=to_email,
                        subject=client_data.subject,
                        body=email_body,
                        is_html=True,
                        from_name=client_data.hr_name,
                        from_email=client_data.hr_email,
                        resume_id=client_data.resume_id,
                        attach_resume=client_data.resume_attachment
                    )
                    successful_sends.append(to_email)
                    print(f"[SUCCESS] Email sent successfully to {to_email}")
                except Exception as email_error:
                    # If attachment fails but we can still send email without it, try that
                    print(f"[WARNING] Email with attachment failed, trying without attachment: {str(email_error)}")
                    try:
                        await send_email(
                            to_email=to_email,
                            subject=client_data.subject,
                            body=email_body,
                            is_html=True,
                            from_name=client_data.hr_name,
                            from_email=client_data.hr_email
                        )
                        successful_sends.append(to_email)
                        print(f"[SUCCESS] Email sent successfully to {to_email} (without attachment)")
                    except Exception as fallback_error:
                        failed_sends.append(f"{to_email}: {str(fallback_error)}")
                        print(f"[ERROR] Failed to send email to {to_email}: {str(fallback_error)}")
            except Exception as e:
                failed_sends.append(f"{to_email}: {str(e)}")
                print(f"[ERROR] Failed to send email to {to_email}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Send email to CC recipients with PDF attachment
        for cc_email in cc_emails:
            try:
                try:
                    await send_email_with_attachment(
                        to_email=cc_email,
                        subject=f"[CC] {client_data.subject}",
                        body=email_body,
                        is_html=True,
                        from_name=client_data.hr_name,
                        from_email=client_data.hr_email,
                        resume_id=client_data.resume_id,
                        attach_resume=client_data.resume_attachment
                    )
                    successful_sends.append(f"{cc_email} (CC)")
                    print(f"[SUCCESS] CC email sent successfully to {cc_email}")
                except Exception as email_error:
                    print(f"[WARNING] CC email with attachment failed, trying without attachment: {str(email_error)}")
                    try:
                        await send_email(
                            to_email=cc_email,
                            subject=f"[CC] {client_data.subject}",
                            body=email_body,
                            is_html=True,
                            from_name=client_data.hr_name,
                            from_email=client_data.hr_email
                        )
                        successful_sends.append(f"{cc_email} (CC)")
                        print(f"[SUCCESS] CC email sent successfully to {cc_email} (without attachment)")
                    except Exception as fallback_error:
                        failed_sends.append(f"{cc_email} (CC): {str(fallback_error)}")
                        print(f"[ERROR] Failed to send CC email to {cc_email}: {str(fallback_error)}")
            except Exception as e:
                failed_sends.append(f"{cc_email} (CC): {str(e)}")
                print(f"[ERROR] Failed to send CC email to {cc_email}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Send email to BCC recipients with PDF attachment
        for bcc_email in bcc_emails:
            try:
                try:
                    await send_email_with_attachment(
                        to_email=bcc_email,
                        subject=f"[BCC] {client_data.subject}",
                        body=email_body,
                        is_html=True,
                        from_name=client_data.hr_name,
                        from_email=client_data.hr_email,
                        resume_id=client_data.resume_id,
                        attach_resume=client_data.resume_attachment
                    )
                    successful_sends.append(f"{bcc_email} (BCC)")
                    print(f"[SUCCESS] BCC email sent successfully to {bcc_email}")
                except Exception as email_error:
                    print(f"[WARNING] BCC email with attachment failed, trying without attachment: {str(email_error)}")
                    try:
                        await send_email(
                            to_email=bcc_email,
                            subject=f"[BCC] {client_data.subject}",
                            body=email_body,
                            is_html=True,
                            from_name=client_data.hr_name,
                            from_email=client_data.hr_email
                        )
                        successful_sends.append(f"{bcc_email} (BCC)")
                        print(f"[SUCCESS] BCC email sent successfully to {bcc_email} (without attachment)")
                    except Exception as fallback_error:
                        failed_sends.append(f"{bcc_email} (BCC): {str(fallback_error)}")
                        print(f"[ERROR] Failed to send BCC email to {bcc_email}: {str(fallback_error)}")
            except Exception as e:
                failed_sends.append(f"{bcc_email} (BCC): {str(e)}")
                print(f"[ERROR] Failed to send BCC email to {bcc_email}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Create resume share records for statistics
        if successful_sends:
            try:
                from app.models.resume_share import ResumeShareModel
                
                share_records = []
                for email in to_emails + cc_emails + bcc_emails:
                    share_record = {
                        "resume_id": client_data.resume_id,
                        "client_email": email,
                        "client_name": client_data.candidate_name,
                        "shared_by": str(current_user["_id"]),
                        "shared_at": datetime.now(timezone.utc),
                        "status": "shared",
                        "email_subject": client_data.subject,
                        "email_sent": True,
                        "attachment_included": client_data.resume_attachment,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    share_records.append(share_record)
                
                if share_records:
                    await db.resume_shares.insert_many(share_records)
                    print(f"[SUCCESS] Created {len(share_records)} resume share records")
            except Exception as e:
                print(f"[WARNING] Failed to create resume share records: {str(e)}")
                import traceback
                traceback.print_exc()

        # Check if any emails were sent successfully
        if not successful_sends and failed_sends:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send emails to all recipients. Errors: {'; '.join(failed_sends)}"
            )
        
        # If some failed but some succeeded, return partial success
        if failed_sends:
            print(f"[WARNING] Partial success: {len(successful_sends)} sent, {len(failed_sends)} failed")
        
        # Determine success message
        if failed_sends:
            message = f"Resume shared with {len(successful_sends)} recipient(s) successfully. {len(failed_sends)} failed."
        else:
            message = "Resume shared with client successfully"
        
        print(f"[SUCCESS] {message}")
        
        return {
            "message": message,
            "recipients": {
                "to": to_emails,
                "cc": cc_emails,
                "bcc": bcc_emails
            },
            "successful_sends": successful_sends,
            "failed_sends": failed_sends if failed_sends else []
        }
        
    except Exception as e:
        print(f"[ERROR] ERROR in client sharing endpoint: {str(e)}")
        print(f"[ERROR] ERROR type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share resume with client: {str(e)}"
        )


@router.post("/test-email")
async def test_email_configuration(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Test email configuration"""
    try:
        from app.core.config import settings
        from app.services.email_service import send_email
        
        # Check configuration
        if settings.use_microsoft365:
            if not all([settings.microsoft_client_id, settings.microsoft_client_secret, 
                       settings.microsoft_tenant_id, settings.microsoft_sender_email]):
                return {
                    "status": "error",
                    "message": "Microsoft 365 configuration incomplete",
                    "details": "Missing required Microsoft 365 OAuth credentials"
                }
        else:
            if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
                missing = []
                if not settings.smtp_host:
                    missing.append("SMTP_HOST")
                if not settings.smtp_username:
                    missing.append("SMTP_USERNAME")
                if not settings.smtp_password:
                    missing.append("SMTP_PASSWORD")
                return {
                    "status": "error", 
                    "message": "SMTP configuration incomplete",
                    "details": f"Missing environment variables: {', '.join(missing)}"
                }
        
        # Try to send a test email
        test_email = current_user.get("email", "test@example.com")
        await send_email(
            to_email=test_email,
            subject="Test Email Configuration",
            body="This is a test email to verify the email service configuration.",
            is_html=False
        )
        
        return {
            "status": "success",
            "message": "Email configuration test successful",
            "details": f"Test email sent to {test_email}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Email configuration test failed",
            "details": str(e)
        }


@router.post("/share-with-client-whatsapp")
async def share_resume_with_client_whatsapp(
    whatsapp_data: ShareWithClientWhatsAppRequest,
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Share resume with client via WhatsApp"""
    
    print(f"[DEBUG] WhatsApp sharing request received")
    print(f"[DEBUG] WhatsApp data: {whatsapp_data}")
    print(f"[DEBUG] Current user: {current_user}")
    
    # Check if WhatsApp is enabled
    if not settings.whatsapp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp service is not enabled. Please contact administrator."
        )
    
    try:
        # Get resume data from database
        db = await get_db()
        resume = await db.resumes.find_one({"_id": ObjectId(whatsapp_data.resume_id)})
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Parse phone numbers
        to_phones = [phone.strip() for phone in whatsapp_data.to_phones.split(',') if phone.strip()]
        
        # Remove empty strings
        to_phones = [phone for phone in to_phones if phone]
        
        print(f"[DEBUG] TO phones: {to_phones}")
        
        # Validate phone numbers
        for phone in to_phones:
            if not whatsapp_service.validate_phone_number(phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid phone number format: {phone}"
                )
        
        # Format phone numbers
        formatted_phones = [whatsapp_service.format_phone_number(phone) for phone in to_phones]
        
        successful_sends = []
        failed_sends = []
        
        # Generate resume URL if not provided
        resume_url = whatsapp_data.resume_url
        if not resume_url and resume.get('file_url'):
            resume_url = f"{settings.backend_base_url}/api/hr/resume/download/{whatsapp_data.resume_id}"
        
        # Send WhatsApp messages
        for i, phone in enumerate(formatted_phones):
            try:
                print(f"[DEBUG] Sending WhatsApp message to {phone}")
                result = await whatsapp_service.send_resume_share_message(
                    to_phone=phone,
                    candidate_name=whatsapp_data.candidate_name,
                    position=whatsapp_data.candidate_position,
                    company_name=whatsapp_data.company_name,
                    hr_name=whatsapp_data.hr_name,
                    hr_phone=whatsapp_data.hr_phone,
                    resume_url=resume_url,
                    additional_message=whatsapp_data.additional_message
                )
                successful_sends.append(phone)
                print(f"[SUCCESS] WhatsApp message sent successfully to {phone}")
            except Exception as e:
                failed_sends.append(f"{phone}: {str(e)}")
                print(f"[ERROR] Failed to send WhatsApp message to {phone}: {str(e)}")
        
        # Create resume share records for statistics
        if successful_sends:
            try:
                from app.models.resume_share import ResumeShareModel
                
                share_records = []
                for phone in to_phones:
                    share_record = {
                        "resume_id": whatsapp_data.resume_id,
                        "client_phone": phone,
                        "client_name": whatsapp_data.candidate_name,
                        "shared_by": str(current_user["_id"]),
                        "shared_at": datetime.now(timezone.utc),
                        "status": "shared",
                        "whatsapp_sent": True,
                        "resume_url_included": bool(resume_url),
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    share_records.append(share_record)
                
                if share_records:
                    await db.resume_shares.insert_many(share_records)
                    print(f"[SUCCESS] Created {len(share_records)} resume share records")
            except Exception as e:
                print(f"[WARNING] Failed to create resume share records: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Check if any messages were sent successfully
        if not successful_sends and failed_sends:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send WhatsApp messages to all recipients. Errors: {'; '.join(failed_sends)}"
            )
        
        # If some failed but some succeeded, return partial success
        if failed_sends:
            print(f"[WARNING] Partial success: {len(successful_sends)} sent, {len(failed_sends)} failed")
        
        # Determine success message
        if failed_sends:
            message = f"Resume shared via WhatsApp with {len(successful_sends)} recipient(s) successfully. {len(failed_sends)} failed."
        else:
            message = "Resume shared with client via WhatsApp successfully"
        
        print(f"[SUCCESS] {message}")
        
        return {
            "message": message,
            "recipients": {
                "phones": to_phones
            },
            "successful_sends": successful_sends,
            "failed_sends": failed_sends if failed_sends else []
        }
        
    except Exception as e:
        print(f"[ERROR] ERROR in WhatsApp sharing endpoint: {str(e)}")
        print(f"[ERROR] ERROR type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share resume with client via WhatsApp: {str(e)}"
        )


@router.post("/test-whatsapp")
async def test_whatsapp_configuration(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Test WhatsApp configuration"""
    try:
        # Check configuration
        if not settings.whatsapp_enabled:
            return {
                "status": "error",
                "message": "WhatsApp service is not enabled",
                "details": "Set WHATSAPP_ENABLED=true in environment variables"
            }
        
        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            missing = []
            if not settings.whatsapp_access_token:
                missing.append("WHATSAPP_ACCESS_TOKEN")
            if not settings.whatsapp_phone_number_id:
                missing.append("WHATSAPP_PHONE_NUMBER_ID")
            return {
                "status": "error",
                "message": "WhatsApp configuration incomplete",
                "details": f"Missing environment variables: {', '.join(missing)}"
            }
        
        # Try to send a test message (you might want to use a test phone number)
        test_phone = current_user.get("phone", "1234567890")  # Replace with actual test phone
        if not whatsapp_service.validate_phone_number(test_phone):
            return {
                "status": "error",
                "message": "Invalid test phone number",
                "details": "Please provide a valid phone number in your profile for testing"
            }
        
        formatted_phone = whatsapp_service.format_phone_number(test_phone)
        await whatsapp_service.send_message(
            to_phone=formatted_phone,
            message="This is a test message to verify the WhatsApp service configuration."
        )
        
        return {
            "status": "success",
            "message": "WhatsApp configuration test successful",
            "details": f"Test message sent to {formatted_phone}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "WhatsApp configuration test failed",
            "details": str(e)
        }


@router.put("/resume-shares/{share_id}")
async def update_resume_share_status(
    share_id: str,
    status_data: dict,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Update the status of a resume share"""
    db = await get_db()
    
    try:
        share_object_id = ObjectId(share_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid share ID"
        )
    
    # Find the resume share record
    share_record = await db.resume_shares.find_one({
        "_id": share_object_id,
        "shared_by": str(current_user["_id"])
    })
    
    if not share_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume share record not found"
        )
    
    # Validate status
    valid_statuses = ["shared", "viewed", "shortlisted", "interview", "offer", "rejected"]
    new_status = status_data.get("status")
    
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Update the status
    update_data = {
        "status": new_status,
        "status_updated_at": datetime.now(timezone.utc),
        "status_updated_by": str(current_user["_id"]),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.resume_shares.update_one(
        {"_id": share_object_id},
        {"$set": update_data}
    )
    
    return {
        "message": "Status updated successfully",
        "share_id": share_id,
        "new_status": new_status,
        "updated_at": update_data["status_updated_at"]
    }
