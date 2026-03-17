from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.services.crypto import encrypt_value
from app.services.email_scan_scheduler import queue_scan_for_inbox
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional
import asyncio

router = APIRouter(prefix="/api/hr/inbox", tags=["Email Inbox"])


class LinkIMAPRequest(BaseModel):
    provider: str  # "gmail", "outlook", "imap"
    imap_host: str
    imap_port: int = 993
    email: EmailStr
    password: str  # or OAuth token
    use_ssl: bool = True
    scan_schedule: str = "daily"  # "daily", "weekly", "monthly"


class InboxResponse(BaseModel):
    id: str
    provider: str
    email: str
    last_scanned_at: Optional[datetime] = None
    scan_schedule: str
    created_at: datetime


@router.post("/link_imap", response_model=InboxResponse)
async def link_imap_inbox(
    inbox_data: LinkIMAPRequest,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Link IMAP inbox for scanning"""
    db = await get_db()
    
    try:
        print(f"DEBUG: current_user type: {type(current_user)}")
        print(f"DEBUG: current_user keys: {list(current_user.keys()) if isinstance(current_user, dict) else 'Not a dict'}")
        print(f"DEBUG: current_user['_id'] type: {type(current_user.get('_id'))}")
        
        # Encrypt sensitive data
        encrypted_password = encrypt_value(inbox_data.password)
        
        # Create inbox document - ensure user_id is converted to string
        user_id = str(current_user["_id"]) if isinstance(current_user["_id"], ObjectId) else current_user["_id"]
        print(f"DEBUG: user_id: {user_id}")
        
        inbox_doc = {
            "user_id": user_id,
            "provider": inbox_data.provider,
            "imap_host": inbox_data.imap_host,
            "imap_port": inbox_data.imap_port,
            "email": inbox_data.email,
            "encrypted_password": encrypted_password,
            "use_ssl": inbox_data.use_ssl,
            "scan_schedule": inbox_data.scan_schedule,
            "is_active": True,
            "last_scanned_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        print(f"DEBUG: About to insert inbox document")
        result = await db.email_inboxes.insert_one(inbox_doc)
        print(f"DEBUG: Insert result: {result.inserted_id}")
        
        # Return created inbox
        created_inbox = await db.email_inboxes.find_one({"_id": result.inserted_id})
        print(f"DEBUG: Created inbox: {created_inbox}")
        
        # Ensure all ObjectId fields are converted to strings
        response = InboxResponse(
            id=str(created_inbox["_id"]),
            provider=created_inbox["provider"],
            email=created_inbox["email"],
            last_scanned_at=created_inbox.get("last_scanned_at"),
            scan_schedule=created_inbox["scan_schedule"],
            created_at=created_inbox["created_at"]
        )
        print(f"DEBUG: Response object: {response}")

        # Queue an initial scan so existing unread resumes are processed automatically
        try:
            queue_scan_for_inbox(str(result.inserted_id))
            print(f"[EMAIL SCAN] Initial scan queued for new inbox {inbox_data.email}")
        except Exception as queue_error:
            print(f"[EMAIL SCAN] Failed to queue initial scan: {queue_error}")

        return response
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link inbox: {str(e)}"
        )


@router.get("/", response_model=list[InboxResponse])
async def get_linked_inboxes(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get all linked inboxes for current HR"""
    db = await get_db()
    
    # Ensure user_id is converted to string
    user_id = str(current_user["_id"]) if isinstance(current_user["_id"], ObjectId) else current_user["_id"]
    
    inboxes = await db.email_inboxes.find({
        "user_id": user_id,
        "is_active": True
    }).to_list(None)
    
    return [
        InboxResponse(
            id=str(inbox["_id"]) if isinstance(inbox["_id"], ObjectId) else inbox["_id"],
            provider=inbox["provider"],
            email=inbox["email"],
            last_scanned_at=inbox.get("last_scanned_at"),
            scan_schedule=inbox["scan_schedule"],
            created_at=inbox["created_at"]
        )
        for inbox in inboxes
    ]


@router.post("/scan_now/{inbox_id}")
async def trigger_immediate_scan(
    inbox_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Trigger immediate scan of inbox"""
    db = await get_db()
    
    try:
        inbox_object_id = ObjectId(inbox_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid inbox ID"
        )
    
    # Get inbox - ensure user_id is converted to string
    user_id = str(current_user["_id"]) if isinstance(current_user["_id"], ObjectId) else current_user["_id"]
    
    inbox = await db.email_inboxes.find_one({
        "_id": inbox_object_id,
        "user_id": user_id
    })
    
    if not inbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbox not found"
        )
    
    try:
        queue_scan_for_inbox(str(inbox_object_id))
        return {"message": "Scan initiated successfully"}
    except Exception as e:
        print(f"[EMAIL SCAN] Failed to queue manual scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate scan: {str(e)}"
        )


@router.delete("/{inbox_id}")
async def delete_inbox(
    inbox_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Delete linked inbox"""
    db = await get_db()
    
    try:
        inbox_object_id = ObjectId(inbox_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid inbox ID"
        )
    
    # Ensure user_id is converted to string
    user_id = str(current_user["_id"]) if isinstance(current_user["_id"], ObjectId) else current_user["_id"]
    
    result = await db.email_inboxes.delete_one({
        "_id": inbox_object_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbox not found"
        )
    
    return {"message": "Inbox deleted successfully"}
