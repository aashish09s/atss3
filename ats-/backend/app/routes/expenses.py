from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.models.expense import ExpenseModel

router = APIRouter(prefix="/api/hr/expenses", tags=["Expenses"])


@router.post("/", response_model=ExpenseModel)
async def add_expense(expense: ExpenseModel, current_user: dict = Depends(require_roles(["hr"]))):
    db = await get_db()
    doc = expense.dict(by_alias=True, exclude_unset=True)
    doc["created_by"] = str(current_user["_id"]) 
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    res = await db.expenses.insert_one(doc)
    created = await db.expenses.find_one({"_id": res.inserted_id})
    if created and created.get("_id"):
        created["_id"] = str(created["_id"])  # ensure string id for pydantic
        created["id"] = str(created["_id"])  # also set id field for frontend compatibility
    return ExpenseModel(**created)


@router.get("/", response_model=List[ExpenseModel])
async def list_expenses(
    category: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    db = await get_db()
    # Admins and accountants can see all expenses, HR users see only their own
    q: Dict[str, Any] = {}
    if current_user["role"] not in ["admin", "accountant"]:
        q["created_by"] = str(current_user["_id"])
    if category:
        q["category"] = category
    if start or end:
        rng: Dict[str, Any] = {}
        if start:
            rng["$gte"] = start
        if end:
            rng["$lte"] = end
        q["date"] = rng
    items = await db.expenses.find(q).sort("date", -1).to_list(length=500)
    cleaned = []
    for e in items:
        if e.get("_id"):
            e["_id"] = str(e["_id"])  # normalize id for client
            e["id"] = str(e["_id"])  # also set id field for frontend compatibility
        cleaned.append(ExpenseModel(**e))
    return cleaned


@router.get("/summary", response_model=Dict[str, float])
async def summary(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    db = await get_db()
    # Admins and accountants can see all expenses, HR users see only their own
    match_exp: Dict[str, Any] = {}
    if current_user["role"] not in ["admin", "accountant"]:
        match_exp["created_by"] = str(current_user["_id"])
    if start or end:
        rng: Dict[str, Any] = {}
        if start:
            rng["$gte"] = start
        if end:
            rng["$lte"] = end
        match_exp["date"] = rng
    exp_pipeline = [
        {"$match": match_exp},
        {"$group": {"_id": None, "total_expenses": {"$sum": "$amount"}}}
    ]
    exp = await db.expenses.aggregate(exp_pipeline).to_list(length=1)
    total_expenses = float(exp[0]["total_expenses"]) if exp else 0.0

    # Income from payments - Admins and accountants can see all, HR see only their own
    match_pay: Dict[str, Any] = {}
    if current_user["role"] not in ["admin", "accountant"]:
        match_pay["created_by"] = str(current_user["_id"])
    if start or end:
        rng2: Dict[str, Any] = {}
        if start:
            rng2["$gte"] = start
        if end:
            rng2["$lte"] = end
        match_pay["payment_date"] = rng2
    pay_pipeline = [
        {"$match": match_pay},
        {"$group": {"_id": None, "total_income": {"$sum": "$amount"}}}
    ]
    pay = await db.payments.aggregate(pay_pipeline).to_list(length=1)
    total_income = float(pay[0]["total_income"]) if pay else 0.0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses
    }


class PaidAmountUpdate(BaseModel):
    paid_amount: float = 0.0


@router.patch("/{expense_id}/paid", response_model=Dict[str, Any])
async def update_expense_paid_amount(
    expense_id: str,
    paid_data: PaidAmountUpdate,
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Update paid amount for an expense"""
    from bson import ObjectId
    
    db = await get_db()
    
    try:
        expense_object_id = ObjectId(expense_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid expense ID")
    
    # Verify expense exists - Admins and accountants can access any expense, HR users see only their own
    expense_query: Dict[str, Any] = {"_id": expense_object_id}
    if current_user["role"] not in ["admin", "accountant"]:
        expense_query["created_by"] = str(current_user["_id"])
    expense = await db.expenses.find_one(expense_query)
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    paid_amt = float(paid_data.paid_amount) if paid_data.paid_amount else 0.0
    
    # Ensure paid amount doesn't exceed total amount
    total_amount = expense.get("amount", 0.0)
    if paid_amt > total_amount:
        paid_amt = total_amount
    
    # Update paid amount
    await db.expenses.update_one(
        {"_id": expense_object_id},
        {
            "$set": {
                "paid_amount": paid_amt,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"success": True, "expense_id": expense_id, "paid_amount": paid_amt}


