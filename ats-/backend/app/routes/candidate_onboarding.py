from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse
from typing import List, Optional
import secrets
import string
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import io
import zipfile

from app.core.config import settings
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.schemas.candidate_onboarding import (
    OnboardingInvitationCreate,
    OnboardingInvitationResponse,
    OnboardingDetailsResponse,
    OnboardingStatus
)
from app.services.storage import StorageService
from app.services.email_service import send_onboarding_email

router = APIRouter()

def generate_onboarding_token():
    """Generate a secure random token for onboarding"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

async def send_onboarding_email_hr(
    candidate_email: str, 
    candidate_name: str, 
    position: str, 
    company_name: str, 
    token: str,
    hr_name: str,
    hr_email: str
):
    """Send onboarding invitation email to candidate using HR user's email as sender"""
    try:
        # Create onboarding URL
        onboarding_url = f"{settings.frontend_base_url}/candidate-onboarding/{token}"
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to {company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {company_name}!</h1>
                    <p>We're excited to have you join our team!</p>
                </div>
                
                <div class="content">
                    <h2>Hello {candidate_name},</h2>
                    
                    <p>Congratulations on your new position as <strong>{position}</strong> at {company_name}!</p>
                    
                    <p>To complete your onboarding process, please click the button below to access your personalized onboarding form:</p>
                    
                    <div style="text-align: center;">
                        <a href="{onboarding_url}" class="button">Complete Onboarding</a>
                    </div>
                    
                    <div class="warning">
                        <strong>Important:</strong> This link is valid for <strong>24 hours only</strong>. 
                        Please complete your onboarding within this timeframe.
                    </div>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact me.</p>
                    
                    <p>We look forward to having you on board!</p>
                    
                    <p>Best regards,<br>
                    {hr_name}<br>
                    HR Team<br>
                    {company_name}</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>If you didn't expect this email, please contact HR immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Use the new email service to send with HR user's email as sender
        print(f"[DEBUG] Calling send_onboarding_email with:")
        print(f"  to_email: {candidate_email}")
        print(f"  candidate_name: {candidate_name}")
        print(f"  hr_name: {hr_name}")
        print(f"  hr_email: {hr_email}")
        print(f"  company_name: {company_name}")
        print(f"  onboarding_url: {onboarding_url}")
        
        await send_onboarding_email(
            to_email=candidate_email,
            candidate_name=candidate_name,
            onboarding_details=f"""
            Position: {position}
            Company: {company_name}
            """,
            hr_name=hr_name,
            hr_email=hr_email,
            company_name=company_name,
            onboarding_url=onboarding_url
        )
        
        print(f"[SUCCESS] Onboarding email sent successfully to {candidate_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Error sending onboarding email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@router.post("/send", response_model=OnboardingInvitationResponse)
async def send_onboarding_invitation(
    invitation_data: OnboardingInvitationCreate,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Send onboarding invitation to candidate"""
    
    print(f"[DEBUG] send_onboarding_invitation called")
    print(f"[DEBUG] invitation_data: {invitation_data}")
    print(f"[DEBUG] current_user: {current_user}")
    print(f"[DEBUG] current_user keys: {list(current_user.keys()) if current_user else 'None'}")
    print(f"[INFO] Sending onboarding invitation to: {invitation_data.candidate_email}")
    
    # Generate secure token
    token = generate_onboarding_token()
    
    # Calculate expiration (24 hours from now)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Create onboarding record
    onboarding_data = {
        "candidate_email": invitation_data.candidate_email,
        "candidate_name": invitation_data.candidate_name,
        "position": invitation_data.position,
        "company_name": invitation_data.company_name,
        "token": token,
        "status": "pending",
        "sent_date": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "hr_user_id": str(current_user["_id"]),
        "hr_email": current_user.get("email", "hr@company.com")
    }
    
    try:
        result = await db.candidate_onboarding.insert_one(onboarding_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create onboarding record: {str(e)}")
    
    # Send email
    try:
        hr_name = current_user.get("full_name") or current_user.get("username") or "HR Team"
        hr_email = current_user.get("email") or "hr@company.com"
        
        email_sent = await send_onboarding_email_hr(
            invitation_data.candidate_email,
            invitation_data.candidate_name,
            invitation_data.position,
            invitation_data.company_name,
            token,
            hr_name,
            hr_email
        )
        
        if not email_sent:
            # If email fails, delete the record
            try:
                await db.candidate_onboarding.delete_one({"_id": result.inserted_id})
            except:
                pass  # Ignore deletion errors
            raise HTTPException(status_code=500, detail="Failed to send onboarding email")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception sending onboarding email: {str(e)}")
        import traceback
        traceback.print_exc()
        # If email fails, delete the record
        try:
            await db.candidate_onboarding.delete_one({"_id": result.inserted_id})
        except:
            pass  # Ignore deletion errors
        raise HTTPException(status_code=500, detail=f"Failed to send onboarding email: {str(e)}")
    
    # Return the created record
    onboarding_data["id"] = str(result.inserted_id)
    return OnboardingInvitationResponse(**onboarding_data)

@router.get("/", response_model=List[OnboardingDetailsResponse])
async def get_onboarding_requests(
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Get all onboarding requests for the current HR user"""
    
    print(f"Getting onboarding requests for user: {current_user['_id']}")
    
    try:
        # Check if requests have expired
        current_time = datetime.now(timezone.utc)
        await db.candidate_onboarding.update_many(
                {
                    "hr_user_id": str(current_user["_id"]),
                    "status": "pending",
                    "expires_at": {"$lt": current_time}
                },
                {"$set": {"status": "expired"}}
            )
        
        # Fetch all requests for this HR user
        cursor = db.candidate_onboarding.find(
            {"hr_user_id": str(current_user["_id"])}
        ).sort("sent_date", -1)
        
        requests = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            requests.append(OnboardingDetailsResponse(**doc))
        
        print(f"Found {len(requests)} onboarding requests")
        return requests
    except Exception as e:
        print(f"Error getting onboarding requests: {e}")
        # If collection doesn't exist or any other error, return empty list
        return []

async def _get_accessible_onboarding_request(db, request_id: str, current_user: dict):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID")

    request = await db.candidate_onboarding.find_one({"_id": ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Onboarding request not found")

    if request["hr_user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    return request

@router.get("/validate/{token}")
async def validate_onboarding_token(
    token: str,
    db = Depends(get_db)
):
    """Validate onboarding token and return invitation details"""
    
    try:
        # Find the onboarding request
        request = await db.candidate_onboarding.find_one({"token": token})
        
        if not request:
            raise HTTPException(status_code=404, detail="Invalid onboarding token")
        
        # Check if expired
        # Handle timezone comparison safely
        current_time = datetime.now(timezone.utc)
        expires_at = request["expires_at"]
        
        # If expires_at is timezone-naive, assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if request["status"] == "pending" and expires_at < current_time:
            # Mark as expired
            try:
                await db.candidate_onboarding.update_one(
                    {"_id": request["_id"]},
                    {"$set": {"status": "expired"}}
                )
            except:
                pass  # Ignore update errors
            raise HTTPException(status_code=400, detail="Onboarding link has expired")
        
        # Check if already completed
        if request["status"] == "completed":
            raise HTTPException(status_code=400, detail="Onboarding already completed")
        
        return {
            "id": str(request["_id"]),
            "candidate_email": request["candidate_email"],
            "candidate_name": request["candidate_name"],
            "position": request["position"],
            "company_name": request["company_name"],
            "status": request["status"],
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/submit/{token}")
async def submit_onboarding_details(
    token: str,
    personal_details_full_name: str = Form(...),
    personal_details_email: str = Form(...),
    personal_details_phone: str = Form(...),
    personal_details_date_of_birth: str = Form(...),
    personal_details_address: str = Form(...),
    personal_details_city: str = Form(...),
    personal_details_state: str = Form(...),
    personal_details_pincode: str = Form(...),
    documents_photo: Optional[UploadFile] = File(None),
    documents_resume: Optional[UploadFile] = File(None),
    documents_degree: Optional[UploadFile] = File(None),
    documents_aadhar_card: Optional[UploadFile] = File(None),
    documents_pan_card: Optional[UploadFile] = File(None),
    documents_id_proof: Optional[UploadFile] = File(None),
    documents_bank_details: Optional[UploadFile] = File(None),
    db = Depends(get_db)
):
    """Submit candidate onboarding details and documents"""
    
    # Validate token
    request = await db.candidate_onboarding.find_one({"token": token})
    
    if not request:
        raise HTTPException(status_code=404, detail="Invalid onboarding token")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Onboarding request is not in pending status")
    
    # Handle timezone comparison safely
    current_time = datetime.now(timezone.utc)
    expires_at = request["expires_at"]
    
    # If expires_at is timezone-naive, assume it's UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < current_time:
        # Mark as expired
        await db.candidate_onboarding.update_one(
            {"_id": request["_id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="Onboarding link has expired")
    
    # Initialize storage service
    storage_service = StorageService()
    
    # Upload documents
    uploaded_documents = {}
    
    document_fields = {
        "photo": documents_photo,
        "resume": documents_resume,
        "degree": documents_degree,
        "aadhar_card": documents_aadhar_card,
        "pan_card": documents_pan_card,
        "id_proof": documents_id_proof,
        "bank_details": documents_bank_details
    }
    
    for field_name, file in document_fields.items():
        if file:
            try:
                # Get file extension from original filename
                original_filename = file.filename
                file_extension = os.path.splitext(original_filename)[1] if original_filename else ''
                
                # Create a clean filename with extension
                clean_filename = f"{field_name}{file_extension}"
                
                # Create path: onboarding/{request_id}/{field_name}.{ext}
                file_path = f"onboarding/{str(request['_id'])}/{clean_filename}"
                
                print(f"Attempting to upload {field_name} to path: {file_path}")
                print(f"Original filename: {original_filename}, Extension: {file_extension}")
                print(f"File object type: {type(file)}")
                print(f"File object attributes: {dir(file)}")
                
                # Get the actual file object from UploadFile
                file_obj = file.file if hasattr(file, 'file') else file
                print(f"File obj type: {type(file_obj)}")
                print(f"File obj attributes: {dir(file_obj)}")
                
                file_url = await storage_service.save_file(file_obj, file_path)
                uploaded_documents[field_name] = file_url
                print(f"Successfully uploaded {field_name}: {file_url}")
                
            except Exception as e:
                print(f"Error uploading {field_name}: {e}")
                print(f"File details - filename: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
                raise HTTPException(status_code=500, detail=f"Failed to upload {field_name}: {str(e)}")
    
    # Prepare personal details
    personal_details = {
        "full_name": personal_details_full_name,
        "email": personal_details_email,
        "phone": personal_details_phone,
        "date_of_birth": personal_details_date_of_birth,
        "address": personal_details_address,
        "city": personal_details_city,
        "state": personal_details_state,
        "pincode": personal_details_pincode
    }
    
    # Update the onboarding request
    update_data = {
        "status": "completed",
        "candidate_details": {
            "personal_details": personal_details,
            "documents": uploaded_documents
        },
        "submitted_at": datetime.now(timezone.utc)
    }
    
    await db.candidate_onboarding.update_one(
        {"_id": request["_id"]},
        {"$set": update_data}
    )
    
    return {"message": "Onboarding details submitted successfully"}

@router.get("/{request_id}/details")
async def get_onboarding_details(
    request_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Get detailed information about a specific onboarding request"""
    
    try:
        request = await _get_accessible_onboarding_request(db, request_id, current_user)
        
        # Convert ObjectId to string and ensure all fields are JSON-serializable
        request["id"] = str(request["_id"])
        request["_id"] = str(request["_id"])
        
        # Convert any remaining ObjectId fields to strings
        if "hr_user_id" in request and isinstance(request["hr_user_id"], ObjectId):
            request["hr_user_id"] = str(request["hr_user_id"])
        
        # Handle datetime fields to ensure they're serializable
        if "expires_at" in request and request["expires_at"]:
            if request["expires_at"].tzinfo is None:
                request["expires_at"] = request["expires_at"].replace(tzinfo=timezone.utc)
            request["expires_at"] = request["expires_at"].isoformat()
        
        if "sent_date" in request and request["sent_date"]:
            if request["sent_date"].tzinfo is None:
                request["sent_date"] = request["sent_date"].replace(tzinfo=timezone.utc)
            request["sent_date"] = request["sent_date"].isoformat()
        
        if "submitted_at" in request and request["submitted_at"]:
            if request["submitted_at"].tzinfo is None:
                request["submitted_at"] = request["submitted_at"].replace(tzinfo=timezone.utc)
            request["submitted_at"] = request["submitted_at"].isoformat()
        
        # Extract and structure the submitted data for frontend consumption
        if "candidate_details" in request:
            # Extract personal details
            if "personal_details" in request["candidate_details"]:
                personal_details = request["candidate_details"]["personal_details"]
                # Map field names to match frontend expectations
                request["personal_details"] = {
                    "full_name": personal_details.get("full_name"),
                    "email": personal_details.get("email"),
                    "phone": personal_details.get("phone"),
                    "dob": personal_details.get("date_of_birth"),  # Map date_of_birth to dob
                    "address": personal_details.get("address"),
                    "city": personal_details.get("city"),
                    "state": personal_details.get("state"),
                    "pincode": personal_details.get("pincode")
                }
            
            # Extract documents
            if "documents" in request["candidate_details"]:
                request["documents"] = request["candidate_details"]["documents"]
        
        return request
        
    except Exception as e:
        print(f"Error getting onboarding details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _resolve_document_path(file_url: str) -> Optional[str]:
    """Resolve a stored document URL to a local filesystem path if available."""
    if not file_url:
        return None

    # Handle full backend URLs (e.g. https://ats.../uploads/....)
    if settings.backend_base_url and file_url.startswith(settings.backend_base_url):
        relative = file_url.split(f"{settings.backend_base_url}/uploads/")[-1]
    elif file_url.startswith("/uploads/"):
        relative = file_url.split("/uploads/")[-1]
    else:
        # Likely a remote URL (e.g. S3); return None to indicate redirect usage
        return None

    local_path = os.path.join(os.path.abspath(settings.local_upload_dir), relative)
    if os.path.exists(local_path):
        return local_path
    return None

@router.get("/{request_id}/documents/{doc_key}")
async def download_onboarding_document(
    request_id: str,
    doc_key: str,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Download a specific onboarding document."""

    request = await _get_accessible_onboarding_request(db, request_id, current_user)

    documents = request.get("candidate_details", {}).get("documents", {})
    if not documents or doc_key not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    file_url = documents[doc_key]
    if not file_url:
        raise HTTPException(status_code=404, detail="Document not found")

    local_path = _resolve_document_path(file_url)
    if local_path:
        filename = os.path.basename(local_path)
        return FileResponse(local_path, media_type="application/octet-stream", filename=filename)

    # Fallback - redirect to original URL (e.g., S3)
    return RedirectResponse(file_url)

@router.get("/{request_id}/documents/archive")
async def download_onboarding_documents_archive(
    request_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Download all onboarding documents as a ZIP archive."""

    request = await _get_accessible_onboarding_request(db, request_id, current_user)

    documents = request.get("candidate_details", {}).get("documents", {})
    if not documents:
        raise HTTPException(status_code=404, detail="No documents available for download")

    zip_buffer = io.BytesIO()
    added_files = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for doc_key, file_url in documents.items():
            if not file_url:
                continue
            local_path = _resolve_document_path(file_url)
            if local_path and os.path.exists(local_path):
                arcname = f"{doc_key}/{os.path.basename(local_path)}"
                zip_file.write(local_path, arcname=arcname)
                added_files += 1

    if added_files == 0:
        raise HTTPException(status_code=404, detail="No downloadable documents found")

    zip_buffer.seek(0)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"onboarding_documents_{request_id}_{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/{request_id}/resend")
async def resend_onboarding_invitation(
    request_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Resend onboarding invitation email to candidate"""
    
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(request_id):
            raise HTTPException(status_code=400, detail="Invalid request ID")
        
        # Find the request
        request = await db.candidate_onboarding.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Onboarding request not found")
        
        # Check if current user is the HR who sent the invitation
        if request["hr_user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if request is still pending
        if request["status"] != "pending":
            raise HTTPException(status_code=400, detail="Can only resend pending invitations")
        
        # Generate new token and expiration
        new_token = generate_onboarding_token()
        new_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Update the request with new token and expiration
        await db.candidate_onboarding.update_one(
            {"_id": ObjectId(request_id)},
            {
                "$set": {
                    "token": new_token,
                    "expires_at": new_expires_at,
                    "sent_date": datetime.now(timezone.utc)
                }
            }
        )
        
        # Resend the email
        hr_name = current_user.get("full_name") or current_user.get("username") or "HR Team"
        hr_email = current_user.get("email") or "hr@company.com"
        
        email_sent = await send_onboarding_email_hr(
            request["candidate_email"],
            request["candidate_name"],
            request["position"],
            request["company_name"],
            new_token,
            hr_name,
            hr_email
        )
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to resend onboarding email")
        
        return {"message": "Onboarding invitation resent successfully"}
        
    except Exception as e:
        print(f"Error resending onboarding invitation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{request_id}")
async def delete_onboarding_request(
    request_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    db = Depends(get_db)
):
    """Delete an onboarding request"""
    
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(request_id):
            raise HTTPException(status_code=400, detail="Invalid request ID")
        
        # Find the request
        request = await db.candidate_onboarding.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Onboarding request not found")
        
        # Check if current user is the HR who sent the invitation
        if request["hr_user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if request is expired (only allow deletion of expired requests)
        if request["status"] != "expired":
            raise HTTPException(status_code=400, detail="Can only delete expired onboarding requests")
        
        # Delete the request
        result = await db.candidate_onboarding.delete_one({"_id": ObjectId(request_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete onboarding request")
        
        return {"message": "Onboarding request deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting onboarding request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
