from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.schemas.resume import ResumeOut
from typing import List

router = APIRouter(prefix="/api/manager/resumes", tags=["Manager - Shared Resumes"])


@router.get("/shared", response_model=List[ResumeOut])
async def get_shared_resumes(
    current_user: dict = Depends(require_roles(["manager"]))
):
    """Get resumes shared with this manager"""
    db = await get_db()
    
    # Get HR users linked to this manager
    hr_users = await db.users.find({
        "manager_id": str(current_user["_id"]),
        "role": "hr"
    }).to_list(None)
    
    if not hr_users:
        return []
    
    hr_user_ids = [str(hr["_id"]) for hr in hr_users]
    
    # Get shared resumes
    resumes = await db.resumes.find({
        "uploaded_by": {"$in": hr_user_ids},
        "shared_with_manager": True
    }).sort("shared_at", -1).to_list(None)
    
    return [
        ResumeOut(
            id=str(resume["_id"]),
            filename=resume["filename"],
            file_url=resume["file_url"],
            uploaded_by=resume["uploaded_by"],
            status=resume["status"],
            parsed_data=resume.get("parsed_data"),
            ats_score=resume.get("ats_score"),
            shared_with_manager=resume.get("shared_with_manager", False),
            created_at=resume["created_at"]
        )
        for resume in resumes
    ]
