from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/api/templates", tags=["Offer Templates"])


class OfferTemplateCreate(BaseModel):
    name: str
    company_logo_url: Optional[str] = None
    theme_color: str = "#3B82F6"
    body_html: str
    placeholders: Dict[str, str] = {}


class OfferTemplateResponse(BaseModel):
    id: str
    name: str
    company_logo_url: Optional[str] = None
    theme_color: str
    body_html: str
    placeholders: Dict[str, str]
    created_by: str
    is_active: bool
    created_at: datetime


@router.post("/", response_model=OfferTemplateResponse)
async def create_template(
    template_data: OfferTemplateCreate,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Create offer letter template"""
    db = await get_db()
    
    template_doc = {
        "name": template_data.name,
        "company_logo_url": template_data.company_logo_url,
        "theme_color": template_data.theme_color,
        "body_html": template_data.body_html,
        "placeholders": template_data.placeholders,
        "created_by": str(current_user["_id"]),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.offer_templates.insert_one(template_doc)
    
    created_template = await db.offer_templates.find_one({"_id": result.inserted_id})
    return OfferTemplateResponse(
        id=str(created_template["_id"]),
        name=created_template["name"],
        company_logo_url=created_template.get("company_logo_url"),
        theme_color=created_template["theme_color"],
        body_html=created_template["body_html"],
        placeholders=created_template["placeholders"],
        created_by=created_template["created_by"],
        is_active=created_template["is_active"],
        created_at=created_template["created_at"]
    )


@router.get("/", response_model=List[OfferTemplateResponse])
async def get_templates(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get all offer templates for current HR"""
    db = await get_db()
    
    # Admins can see all templates, HR users see only their own
    template_query: Dict[str, Any] = {"is_active": True}
    if current_user["role"] != "admin":
        template_query["created_by"] = str(current_user["_id"])
    templates = await db.offer_templates.find(template_query).sort("created_at", -1).to_list(None)
    
    return [
        OfferTemplateResponse(
            id=str(template["_id"]),
            name=template["name"],
            company_logo_url=template.get("company_logo_url"),
            theme_color=template["theme_color"],
            body_html=template["body_html"],
            placeholders=template["placeholders"],
            created_by=template["created_by"],
            is_active=template["is_active"],
            created_at=template["created_at"]
        )
        for template in templates
    ]


@router.patch("/{template_id}", response_model=OfferTemplateResponse)
async def update_template(
    template_id: str,
    template_data: OfferTemplateCreate,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Update offer template"""
    db = await get_db()
    
    try:
        template_object_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template ID"
        )
    
    # Check if template exists and belongs to user
    # Admins can see any template, HR users see only their own
    template_query: Dict[str, Any] = {"_id": template_object_id}
    if current_user["role"] != "admin":
        template_query["created_by"] = str(current_user["_id"])
    template = await db.offer_templates.find_one(template_query)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Update template
    update_data = {
        "name": template_data.name,
        "company_logo_url": template_data.company_logo_url,
        "theme_color": template_data.theme_color,
        "body_html": template_data.body_html,
        "placeholders": template_data.placeholders,
        "updated_at": datetime.utcnow()
    }
    
    await db.offer_templates.update_one(
        {"_id": template_object_id},
        {"$set": update_data}
    )
    
    # Return updated template
    updated_template = await db.offer_templates.find_one({"_id": template_object_id})
    return OfferTemplateResponse(
        id=str(updated_template["_id"]),
        name=updated_template["name"],
        company_logo_url=updated_template.get("company_logo_url"),
        theme_color=updated_template["theme_color"],
        body_html=updated_template["body_html"],
        placeholders=updated_template["placeholders"],
        created_by=updated_template["created_by"],
        is_active=updated_template["is_active"],
        created_at=updated_template["created_at"]
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Delete offer template"""
    db = await get_db()
    
    try:
        template_object_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template ID"
        )
    
    # Admins can delete any template, HR users can delete only their own
    delete_query: Dict[str, Any] = {"_id": template_object_id}
    if current_user["role"] != "admin":
        delete_query["created_by"] = str(current_user["_id"])
    result = await db.offer_templates.update_one(
        delete_query,
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return {"message": "Template deleted successfully"}
