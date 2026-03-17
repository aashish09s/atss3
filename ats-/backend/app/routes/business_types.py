from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.models.business_type import BusinessTypeModel
from bson import ObjectId

router = APIRouter(prefix="/api/hr/business-types", tags=["Business Types"])


@router.get("/", response_model=List[BusinessTypeModel])
async def list_business_types():
    db = await get_db()
    items = await db.business_types.find({"active": True}).sort("name", 1).to_list(length=100)
    # Convert ObjectId to string for Pydantic
    cleaned_items = []
    for it in items:
        if it.get("_id"):
            it["_id"] = str(it["_id"])
            it["id"] = str(it["_id"])
        cleaned_items.append(it)
    return [BusinessTypeModel(**it) for it in cleaned_items]


@router.get("/{code}", response_model=BusinessTypeModel)
async def get_business_type(code: str):
    db = await get_db()
    bt = await db.business_types.find_one({"code": code, "active": True})
    if not bt:
        raise HTTPException(status_code=404, detail="Business type not found")
    # Convert ObjectId to string
    if bt.get("_id"):
        bt["_id"] = str(bt["_id"])
        bt["id"] = str(bt["_id"])
    return BusinessTypeModel(**bt)


@router.post("/", response_model=BusinessTypeModel)
async def create_business_type(data: BusinessTypeModel, current_user: dict = Depends(require_roles(["admin", "hr"]))):
    db = await get_db()
    exists = await db.business_types.find_one({"$or": [{"code": data.code}, {"prefix": data.prefix}]})
    if exists:
        raise HTTPException(status_code=400, detail="Business type with same code/prefix already exists")
    # Create document - only include fields that should be in the database
    doc = {
        "code": data.code,
        "name": data.name,
        "prefix": data.prefix,
        "default_tax_rate": data.default_tax_rate,
        "active": data.active if data.active is not None else True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res = await db.business_types.insert_one(doc)
    created = await db.business_types.find_one({"_id": res.inserted_id})
    # Convert ObjectId to string
    if created and created.get("_id"):
        created["_id"] = str(created["_id"])
        created["id"] = str(created["_id"])
    return BusinessTypeModel(**created)


@router.post("/seed-defaults", response_model=dict)
async def seed_defaults():
    db = await get_db()
    # If already present, do nothing (idempotent and open for first-time bootstrap)
    existing_count = await db.business_types.count_documents({})
    if existing_count > 0:
        return {"inserted": 0, "message": "business_types already present"}
    defaults = [
        {"code": "third_party_payroll", "name": "Third-Party Payroll", "prefix": "tpp", "default_tax_rate": 18.0},
        {"code": "payroll_mgmt", "name": "Payroll Management", "prefix": "pm", "default_tax_rate": 18.0},
        {"code": "compliance_mgmt", "name": "Compliance Management", "prefix": "cm", "default_tax_rate": 18.0},
        {"code": "recruitment", "name": "Recruitment", "prefix": "rec", "default_tax_rate": 18.0},
        {"code": "task_mgmt", "name": "Task Management", "prefix": "tm", "default_tax_rate": 18.0},
        {"code": "licensing_reg", "name": "Licensing & Registration", "prefix": "lr", "default_tax_rate": 18.0},
    ]
    inserted = 0
    for d in defaults:
        exists = await db.business_types.find_one({"code": d["code"]})
        if not exists:
            d["created_at"] = datetime.utcnow()
            d["updated_at"] = datetime.utcnow()
            await db.business_types.insert_one(d)
            inserted += 1
    return {"inserted": inserted}


@router.put("/{bt_id}", response_model=BusinessTypeModel)
async def update_business_type(bt_id: str, data: BusinessTypeModel, current_user: dict = Depends(require_roles(["admin", "hr"]))):
    db = await get_db()
    try:
        _id = ObjectId(bt_id)
    except Exception:
        raise HTTPException(400, "Invalid id")
    payload = data.dict(by_alias=True, exclude_unset=True)
    payload.pop("_id", None)
    payload["updated_at"] = datetime.utcnow()
    await db.business_types.update_one({"_id": _id}, {"$set": payload})
    doc = await db.business_types.find_one({"_id": _id})
    if not doc:
        raise HTTPException(404, "Not found")
    # Convert ObjectId to string
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
        doc["id"] = str(doc["_id"])
    return BusinessTypeModel(**doc)


@router.delete("/{bt_id}", response_model=dict)
async def delete_business_type(bt_id: str, current_user: dict = Depends(require_roles(["admin"]))):
    db = await get_db()
    try:
        _id = ObjectId(bt_id)
    except Exception:
        raise HTTPException(400, "Invalid id")
    await db.business_types.update_one({"_id": _id}, {"$set": {"active": False, "updated_at": datetime.utcnow()}})
    return {"message": "deleted"}


