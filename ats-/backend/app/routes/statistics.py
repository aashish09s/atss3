from fastapi import APIRouter, Depends
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


@router.get("/hr-dashboard")
async def get_hr_dashboard_stats(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get HR dashboard statistics"""
    db = await get_db()
    user_id = str(current_user["_id"])

    # Get date ranges
    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)

    base_resume_query: Dict[str, Any] = {"uploaded_by": user_id}
    recent_projection = {
        "filename": 1,
        "parsed_data.name": 1,
        "status": 1,
        "created_at": 1
    }

    # Kick off all Mongo calls concurrently
    (
        total_resumes,
        resumes_this_week,
        total_jds,
        active_jds,
        inactive_jds,
        status_counts,
        ats_stats,
        recent_resumes
    ) = await asyncio.gather(
        db.resumes.count_documents(base_resume_query),
        db.resumes.count_documents({**base_resume_query, "created_at": {"$gte": week_ago}}),
        db.jds.count_documents({"uploaded_by": user_id}),
        db.jds.count_documents({"uploaded_by": user_id, "is_active": True}),
        db.jds.count_documents({"uploaded_by": user_id, "is_active": False}),
        db.resumes.aggregate([
            {"$match": base_resume_query},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]).to_list(None),
        db.resumes.aggregate([
            {"$match": {**base_resume_query, "ats_score": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": None,
                "avg_score": {"$avg": "$ats_score"},
                "max_score": {"$max": "$ats_score"},
                "min_score": {"$min": "$ats_score"}
            }}
        ]).to_list(None),
        db.resumes
        .find(base_resume_query, recent_projection)
        .sort("created_at", -1)
        .limit(5)
        .to_list(None)
    )

    status_dict = {item["_id"]: item["count"] for item in status_counts}
    ats_data = ats_stats[0] if ats_stats else {"avg_score": 0, "max_score": 0, "min_score": 0}

    return {
        "total_resumes": total_resumes,
        "resumes_this_week": resumes_this_week,
        "total_jds": total_jds,
        "active_jds": active_jds,
        "inactive_jds": inactive_jds,
        "status_breakdown": {
            "submission": status_dict.get("submission", 0),
            "shortlisting": status_dict.get("shortlisting", 0),
            "interview": status_dict.get("interview", 0),
            "select": status_dict.get("select", 0),
            "reject": status_dict.get("reject", 0),
            "offer_letter": status_dict.get("offer_letter", 0),
            "onboarding": status_dict.get("onboarding", 0)
        },
        "ats_statistics": {
            "average_score": round(ats_data.get("avg_score", 0) or 0, 1),
            "highest_score": ats_data.get("max_score") or 0,
            "lowest_score": ats_data.get("min_score") or 0
        },
        "recent_uploads": [
            {
                "id": str(resume.get("_id")),
                "filename": resume.get("filename"),
                "candidate_name": resume.get("parsed_data", {}).get("name", "Unknown"),
                "status": resume.get("status"),
                "created_at": resume.get("created_at")
            }
            for resume in recent_resumes
        ]
    }


@router.get("/manager-dashboard")
async def get_manager_dashboard_stats(
    current_user: dict = Depends(require_roles(["manager"]))
):
    """Get Manager dashboard statistics"""
    db = await get_db()
    
    # Get HR users linked to this manager
    hr_users = await db.users.find({
        "manager_id": str(current_user["_id"]),
        "role": "hr"
    }).to_list(None)
    
    if not hr_users:
        return {
            "shared_resumes": 0,
            "pending_review": 0,
            "approved": 0,
            "rejected": 0,
            "interviews_scheduled": 0,
            "recent_actions": []
        }
    
    hr_user_ids = [str(hr["_id"]) for hr in hr_users]
    
    # Get shared resumes statistics
    shared_resumes = await db.resumes.count_documents({
        "uploaded_by": {"$in": hr_user_ids},
        "shared_with_manager": True
    })
    
    # Status counts for shared resumes
    status_pipeline = [
        {
            "$match": {
                "uploaded_by": {"$in": hr_user_ids},
                "shared_with_manager": True
            }
        },
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = await db.resumes.aggregate(status_pipeline).to_list(None)
    status_dict = {item["_id"]: item["count"] for item in status_counts}
    
    # Recent shared resumes
    recent_shared = await db.resumes.find({
        "uploaded_by": {"$in": hr_user_ids},
        "shared_with_manager": True
    }).sort("shared_at", -1).limit(5).to_list(None)
    
    return {
        "shared_resumes": shared_resumes,
        "pending_review": status_dict.get("submission", 0) + status_dict.get("shortlisting", 0),
        "approved": status_dict.get("select", 0),
        "rejected": status_dict.get("reject", 0),
        "interviews_scheduled": status_dict.get("interview", 0),
        "recent_shared": [
            {
                "id": str(resume["_id"]),
                "filename": resume["filename"],
                "candidate_name": resume.get("parsed_data", {}).get("name", "Unknown"),
                "status": resume["status"],
                "shared_at": resume.get("shared_at")
            }
            for resume in recent_shared
        ]
    }


@router.get("/admin-dashboard")
async def get_admin_dashboard_stats(
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Get Admin dashboard statistics"""
    db = await get_db()
    
    # User counts
    total_users = await db.users.count_documents({"role": {"$ne": "admin"}})
    hr_count = await db.users.count_documents({"role": "hr"})
    manager_count = await db.users.count_documents({"role": "manager"})
    
    # Linked HR count
    linked_hr = await db.users.count_documents({
        "role": "hr",
        "manager_id": {"$exists": True, "$ne": None}
    })
    
    # Total resumes in system
    total_resumes = await db.resumes.count_documents({})
    
    # Total JDs
    total_jds = await db.jds.count_documents({})
    
    # Account requests
    pending_requests = await db.account_requests.count_documents({"status": "pending"})
    
    # Recent users
    recent_users = await db.users.find({
        "role": {"$ne": "admin"}
    }).sort("created_at", -1).limit(5).to_list(None)
    
    return {
        "total_users": total_users,
        "hr_users": hr_count,
        "manager_users": manager_count,
        "linked_hr_users": linked_hr,
        "total_resumes": total_resumes,
        "total_job_descriptions": total_jds,
        "pending_account_requests": pending_requests,
        "recent_users": [
            {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "created_at": user["created_at"],
                "is_linked": bool(user.get("manager_id")) if user["role"] == "hr" else False
            }
            for user in recent_users
        ]
    }


@router.get("/system-health")
async def get_system_health_stats(
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Get system health statistics"""
    db = await get_db()
    
    # Database collections stats
    collections_stats = {}
    for collection_name in ["users", "resumes", "jds", "parsed_resumes", "email_inboxes"]:
        try:
            count = await db[collection_name].count_documents({})
            collections_stats[collection_name] = count
        except Exception as e:
            collections_stats[collection_name] = f"Error: {str(e)}"
    
    # Recent activity across the system
    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)
    
    recent_activity = {
        "resumes_uploaded_this_week": await db.resumes.count_documents({
            "created_at": {"$gte": week_ago}
        }),
        "jds_created_this_week": await db.jds.count_documents({
            "created_at": {"$gte": week_ago}
        }),
        "users_created_this_week": await db.users.count_documents({
            "created_at": {"$gte": week_ago},
            "role": {"$ne": "admin"}
        })
    }
    
    return {
        "collections_stats": collections_stats,
        "recent_activity": recent_activity,
        "system_status": "healthy"
    }
