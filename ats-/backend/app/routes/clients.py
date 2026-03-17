from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/api/hr/clients", tags=["Clients"])


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    company: str


class ClientOut(BaseModel):
    id: str
    name: str
    email: str
    company: str
    created_at: datetime
    created_by: str
    created_by_role: Optional[str] = None


async def _get_admin_user_ids(db) -> List[str]:
    admin_users = await db.users.find({"role": "admin"}, {"_id": 1}).to_list(None)
    return [str(user["_id"]) for user in admin_users]


def _client_projection() -> Dict[str, int]:
    return {
        "name": 1,
        "email": 1,
        "company": 1,
        "created_at": 1,
        "created_by": 1,
        "created_by_role": 1
    }


async def _get_accessible_clients(db, current_user: dict) -> List[Dict[str, Any]]:
    user_id = str(current_user["_id"])
    base_query: Dict[str, Any] = {"is_active": True}

    if current_user["role"] == "admin":
        clients = await db.clients.find(base_query, _client_projection()).sort("created_at", -1).to_list(None)
    else:
        admin_ids = await _get_admin_user_ids(db)
        or_filters = [
            {"created_by": user_id},
            {"created_by_role": "admin"}
        ]
        if admin_ids:
            or_filters.append({"created_by": {"$in": admin_ids}})
        base_query["$or"] = or_filters
        clients = await db.clients.find(base_query, _client_projection()).sort("created_at", -1).to_list(None)

    return clients


async def _find_accessible_client(db, current_user: dict, client_object_id: ObjectId) -> Optional[Dict[str, Any]]:
    base_filter: Dict[str, Any] = {
        "_id": client_object_id,
        "is_active": True
    }

    if current_user["role"] == "admin":
        return await db.clients.find_one(base_filter)

    admin_ids = await _get_admin_user_ids(db)
    or_filters = [
        {"created_by": str(current_user["_id"])},
        {"created_by_role": "admin"}
    ]
    if admin_ids:
        or_filters.append({"created_by": {"$in": admin_ids}})
    base_filter["$or"] = or_filters
    return await db.clients.find_one(base_filter)


@router.post("/", response_model=ClientOut)
async def create_client(
    client_data: ClientCreate,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Create a new client"""
    db = await get_db()

    # Check if client already exists
    existing_client = await db.clients.find_one({"email": client_data.email})
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client with this email already exists"
        )

    # Create new client
    new_client = {
        "name": client_data.name,
        "email": client_data.email,
        "company": client_data.company,
        "created_by": str(current_user["_id"]),
        "created_by_role": current_user.get("role", "hr"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }

    result = await db.clients.insert_one(new_client)

    # Return created client
    created_client = await db.clients.find_one({"_id": result.inserted_id})
    return ClientOut(
        id=str(created_client["_id"]),
        name=created_client["name"],
        email=created_client["email"],
        company=created_client["company"],
        created_at=created_client["created_at"],
        created_by=created_client["created_by"],
        created_by_role=created_client.get("created_by_role")
    )


@router.get("/", response_model=List[ClientOut])
async def get_clients(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get clients accessible to the current user"""
    db = await get_db()

    clients = await _get_accessible_clients(db, current_user)

    return [
        ClientOut(
            id=str(client["_id"]),
            name=client["name"],
            email=client["email"],
            company=client["company"],
            created_at=client["created_at"],
            created_by=client["created_by"],
            created_by_role=client.get("created_by_role")
        )
        for client in clients
    ]


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get a specific client by ID"""
    db = await get_db()

    try:
        client_object_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )

    client = await _find_accessible_client(db, current_user, client_object_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    return ClientOut(
        id=str(client["_id"]),
        name=client["name"],
        email=client["email"],
        company=client["company"],
        created_at=client["created_at"],
        created_by=client["created_by"],
        created_by_role=client.get("created_by_role")
    )


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Delete a client (soft delete)"""
    db = await get_db()

    try:
        client_object_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )

    client_filter = {"_id": client_object_id}
    if current_user["role"] != "admin":
        client_filter["created_by"] = str(current_user["_id"])

    client = await db.clients.find_one(client_filter)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Soft delete (mark as inactive)
    await db.clients.update_one(
        {"_id": client_object_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )

    return {"message": "Client deleted successfully"}


@router.get("/{client_id}/stats")
async def get_client_statistics(
    client_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get statistics for a specific client"""
    db = await get_db()

    try:
        client_object_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )

    client = await _find_accessible_client(db, current_user, client_object_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    client_email = client["email"]

    resume_filter = {
        "client_email": client_email
    }
    if current_user["role"] != "admin":
        resume_filter["shared_by"] = str(current_user["_id"])

    total_resumes = await db.resume_shares.count_documents(resume_filter)

    shortlisted = await db.resume_shares.count_documents({
        **resume_filter,
        "status": "shortlisted"
    })

    interviews = await db.resume_shares.count_documents({
        **resume_filter,
        "status": "interview"
    })

    offers = await db.resume_shares.count_documents({
        **resume_filter,
        "status": "offer"
    })

    return {
        "client_id": client_id,
        "client_name": client["name"],
        "client_email": client_email,
        "total_resumes": total_resumes,
        "shortlisted": shortlisted,
        "interviews": interviews,
        "offers": offers
    }


@router.get("/bulk-stats")
async def get_clients_bulk_stats(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get statistics for all accessible clients in a single request"""
    db = await get_db()

    clients = await _get_accessible_clients(db, current_user)

    if not clients:
        return {
            "client_stats": {},
            "summary": {
                "total_clients": 0,
                "total_resumes": 0,
                "shortlisted": 0,
                "interviews": 0,
                "offers": 0
            }
        }

    email_to_client = {client["email"]: client for client in clients}
    client_emails = list(email_to_client.keys())

    stats_by_email: Dict[str, Dict[str, int]] = {}

    if client_emails:
        resume_filter: Dict[str, Any] = {
            "client_email": {"$in": client_emails}
        }
        if current_user["role"] != "admin":
            resume_filter["shared_by"] = str(current_user["_id"])

        pipeline = [
            {"$match": resume_filter},
            {"$group": {
                "_id": "$client_email",
                "total_resumes": {"$sum": 1},
                "shortlisted": {"$sum": {"$cond": [{"$eq": ["$status", "shortlisted"]}, 1, 0]}},
                "interviews": {"$sum": {"$cond": [{"$eq": ["$status", "interview"]}, 1, 0]}},
                "offers": {"$sum": {"$cond": [{"$eq": ["$status", "offer"]}, 1, 0]}}
            }}
        ]

        stats_results = await db.resume_shares.aggregate(pipeline).to_list(None)
        for item in stats_results:
            email = item["_id"]
            stats_by_email[email] = {
                "total_resumes": item.get("total_resumes", 0),
                "shortlisted": item.get("shortlisted", 0),
                "interviews": item.get("interviews", 0),
                "offers": item.get("offers", 0)
            }

    client_stats: Dict[str, Dict[str, int]] = {}
    summary = {
        "total_clients": len(clients),
        "total_resumes": 0,
        "shortlisted": 0,
        "interviews": 0,
        "offers": 0
    }

    for client in clients:
        stats = stats_by_email.get(client["email"], {
            "total_resumes": 0,
            "shortlisted": 0,
            "interviews": 0,
            "offers": 0
        })
        client_id = str(client["_id"])
        client_stats[client_id] = stats

        summary["total_resumes"] += stats["total_resumes"]
        summary["shortlisted"] += stats["shortlisted"]
        summary["interviews"] += stats["interviews"]
        summary["offers"] += stats["offers"]

    return {
        "client_stats": client_stats,
        "summary": summary
    }


@router.get("/{client_id}/shared-resumes")
async def get_client_shared_resumes(
    client_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get resumes shared with a specific client"""
    db = await get_db()

    try:
        client_object_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )

    client = await _find_accessible_client(db, current_user, client_object_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    client_email = client["email"]

    shared_filter = {
        "client_email": client_email
    }
    if current_user["role"] != "admin":
        shared_filter["shared_by"] = str(current_user["_id"])

    shared_resumes = await db.resume_shares.find(shared_filter).sort("shared_at", -1).to_list(None)

    resume_details = []
    for share in shared_resumes:
        resume = await db.resumes.find_one({"_id": ObjectId(share["resume_id"])})
        if resume:
            resume_details.append({
                "share_id": str(share["_id"]),
                "resume_id": str(resume["_id"]),
                "filename": resume["filename"],
                "file_url": resume["file_url"],
                "candidate_name": resume.get("parsed_data", {}).get("name", "Unknown"),
                "candidate_email": resume.get("parsed_data", {}).get("email", ""),
                "candidate_phone": resume.get("parsed_data", {}).get("phone", ""),
                "skills": resume.get("parsed_data", {}).get("skills", []),
                "experience": resume.get("parsed_data", {}).get("experience", []),
                "education": resume.get("parsed_data", {}).get("education", []),
                "ats_score": resume.get("ats_score"),
                "resume_status": resume.get("status", "submission"),
                "shared_at": share["shared_at"],
                "share_status": share["status"],
                "status_updated_at": share.get("status_updated_at"),
                "email_subject": share.get("email_subject"),
                "email_sent": share.get("email_sent", True),
                "attachment_included": share.get("attachment_included", True)
            })

    return {
        "client_id": client_id,
        "client_name": client["name"],
        "client_email": client_email,
        "total_shared": len(resume_details),
        "shared_resumes": resume_details
    }


@router.get("/overall-stats")
async def get_overall_client_statistics(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get overall statistics for all clients"""
    db = await get_db()
    clients = await _get_accessible_clients(db, current_user)

    total_clients = len(clients)
    client_emails = [client["email"] for client in clients]

    resume_filter = {
        "client_email": {"$in": client_emails}
    } if client_emails else {}

    if current_user["role"] != "admin":
        resume_filter["shared_by"] = str(current_user["_id"])

    total_resumes_shared = await db.resume_shares.count_documents(resume_filter) if resume_filter else 0
    total_shortlisted = await db.resume_shares.count_documents({
        **resume_filter,
        "status": "shortlisted"
    }) if resume_filter else 0
    total_interviews = await db.resume_shares.count_documents({
        **resume_filter,
        "status": "interview"
    }) if resume_filter else 0
    total_offers = await db.resume_shares.count_documents({
        **resume_filter,
        "status": "offer"
    }) if resume_filter else 0

    return {
        "total_clients": total_clients,
        "total_resumes": total_resumes_shared,
        "shortlisted": total_shortlisted,
        "interviews": total_interviews,
        "offers": total_offers
    }
