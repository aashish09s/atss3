from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.models.payment import PaymentModel, PaymentCreate

router = APIRouter(prefix="/api/hr/ledger", tags=["Ledger"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_ledger(
    invoice_number: Optional[str] = None,
    client_name: Optional[str] = None,
    payment_status: Optional[str] = Query(None, regex="^(paid|partial|pending)$"),
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    db = await get_db()
    user_id = str(current_user["_id"])
    
    # Admins and accountants can see all invoices, HR users see only their own
    match: Dict[str, Any] = {
        "status": {"$in": ["sent", "paid"]}  # Only show sent or paid invoices
    }
    if current_user["role"] not in ["admin", "accountant"]:
        match["created_by"] = user_id
    
    # Debug logging
    total_invoices = await db.invoices.count_documents(match)
    print(f"[LEDGER LIST] User {user_id} ({current_user['role']}) has {total_invoices} total invoices")
    if invoice_number and invoice_number.strip():
        match["invoice_number"] = {"$regex": invoice_number.strip(), "$options": "i"}
    if client_name and client_name.strip():
        match["client_name"] = {"$regex": client_name.strip(), "$options": "i"}
    
    print(f"[LEDGER LIST] Match query: {match}")

    pipeline = [
        {"$match": match},
        {"$lookup": {
            "from": "payments",
            "let": {"inv_id": {"$toString": "$_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$invoice_id", {"$toString": "$$inv_id"}]}}},
                {"$group": {"_id": "$invoice_id", "received": {"$sum": "$amount"}}}
            ],
            "as": "payment_summary"
        }},
        {"$addFields": {
            "received_amount": {"$ifNull": [{"$arrayElemAt": ["$payment_summary.received", 0]}, 0]},
            "tds_amount": {"$ifNull": ["$tds_amount", 0]},
            "outstanding": {
                "$subtract": [
                    "$total_amount",
                    {
                        "$add": [
                            {"$ifNull": [{"$arrayElemAt": ["$payment_summary.received", 0]}, 0]},
                            {"$ifNull": ["$tds_amount", 0]}
                        ]
                    }
                ]
            }
        }}
    ]

    items: List[Dict[str, Any]] = []
    row_count = 0
    async for row in db.invoices.aggregate(pipeline):
        row_count += 1
        try:
            status = "pending"
            received_amount = row.get("received_amount", 0.0)
            total_amount = row.get("total_amount", 0.0)
            
            if received_amount == 0:
                status = "pending"
            elif received_amount < total_amount:
                status = "partial"
            else:
                status = "paid"
                
            if payment_status and payment_status != status:
                continue
                
            items.append({
                "id": str(row.get("_id", "")),
                "invoice_number": row.get("invoice_number", ""),
                "client_name": row.get("client_name", ""),
                "invoice_date": row.get("invoice_date"),
                "total_amount": float(total_amount) if total_amount else 0.0,
                "received_amount": float(received_amount) if received_amount else 0.0,
                "tds_amount": float(row.get("tds_amount", 0.0)) if row.get("tds_amount") else 0.0,
                "outstanding": float(row.get("outstanding", 0.0)) if row.get("outstanding") else 0.0,
                "status": status,
            })
        except Exception as e:
            print(f"[LEDGER ERROR] Failed to process invoice row: {str(e)}")
            print(f"[LEDGER ERROR] Row data: {row}")
            continue
    
    print(f"[LEDGER LIST] Processed {row_count} invoice rows, returning {len(items)} items")
    return items


@router.get("/summary", response_model=Dict[str, float])
async def summary(current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))):
    db = await get_db()
    user_id = str(current_user["_id"])
    
    # Admins and accountants can see all invoices, HR users see only their own
    match_query: Dict[str, Any] = {"status": {"$in": ["sent", "paid"]}}
    if current_user["role"] not in ["admin", "accountant"]:
        match_query["created_by"] = user_id
    
    # Debug: Count total invoices
    total_count = await db.invoices.count_documents(match_query)
    print(f"[LEDGER DEBUG] User {user_id} ({current_user['role']}) has {total_count} sent/paid invoices")
    
    # Include only sent/paid invoices in summary
    pipeline = [
        {"$match": match_query},
        {"$group": {
            "_id": None,
            "total_invoiced": {"$sum": {"$ifNull": ["$total_amount", 0]}}
        }}
    ]
    inv_summary = await db.invoices.aggregate(pipeline).to_list(length=1)
    total_invoiced = float(inv_summary[0]["total_invoiced"]) if inv_summary and len(inv_summary) > 0 else 0.0
    print(f"[LEDGER DEBUG] Total invoiced: {total_invoiced}")

    pay_pipeline = [
        {"$match": {"created_by": user_id}},
        {"$group": {"_id": None, "total_received": {"$sum": {"$ifNull": ["$amount", 0]}}}}
    ]
    pay_summary = await db.payments.aggregate(pay_pipeline).to_list(length=1)
    total_received = float(pay_summary[0]["total_received"]) if pay_summary and len(pay_summary) > 0 else 0.0

    # Calculate total TDS
    tds_pipeline = [
        {"$match": {
            "created_by": user_id,
            "status": {"$in": ["sent", "paid"]}
        }},
        {"$group": {
            "_id": None,
            "total_tds": {"$sum": {"$ifNull": ["$tds_amount", 0]}}
        }}
    ]
    tds_summary = await db.invoices.aggregate(tds_pipeline).to_list(length=1)
    total_tds = float(tds_summary[0]["total_tds"]) if tds_summary and len(tds_summary) > 0 else 0.0
    
    return {
        "total_invoiced": total_invoiced,
        "total_received": total_received,
        "total_tds": total_tds,
        "total_outstanding": total_invoiced - total_received - total_tds
    }


@router.get("/{invoice_id}/payments", response_model=List[PaymentModel])
async def list_payments(invoice_id: str, current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))):
    db = await get_db()
    # Admins and accountants can see all payments, HR users see only their own
    payment_query: Dict[str, Any] = {"invoice_id": invoice_id}
    if current_user["role"] not in ["admin", "accountant"]:
        payment_query["created_by"] = str(current_user["_id"])
    payments = await db.payments.find(payment_query).sort("payment_date", -1).to_list(length=200)
    cleaned = []
    for p in payments:
        if p.get("_id"):
            p["_id"] = str(p["_id"])  # normalize ObjectId for pydantic
        cleaned.append(PaymentModel(**p))
    return cleaned


@router.post("/{invoice_id}/payments", response_model=PaymentModel)
async def add_payment(invoice_id: str, payment: PaymentCreate, current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))):
    db = await get_db()
    # Admins and accountants can add payments to any invoice, HR users can only add to their own
    invoice_query: Dict[str, Any] = {"_id": ObjectId(invoice_id)}
    if current_user["role"] not in ["admin", "accountant"]:
        invoice_query["created_by"] = str(current_user["_id"])
    inv = await db.invoices.find_one(invoice_query)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    doc = payment.dict(by_alias=True, exclude_unset=True)
    doc["invoice_id"] = invoice_id
    doc["invoice_number"] = inv.get("invoice_number")
    doc["client_name"] = inv.get("client_name")
    doc["created_by"] = str(current_user["_id"]) 
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    res = await db.payments.insert_one(doc)
    created = await db.payments.find_one({"_id": res.inserted_id})
    if created and created.get("_id"):
        created["_id"] = str(created["_id"])  # normalize id
    return PaymentModel(**created)


