from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Body, Query
from pydantic import BaseModel, field_validator
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.services.ai_service import parse_job_description, score_resume_against_jd
from app.services.ner_resume_service import score_resume_with_ner, score_multiple_resumes_with_ner
from app.utils.text_extraction import extract_text_from_file
from app.utils.file_utils import save_upload_file_tmp, validate_resume_file
from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import os
import uuid
import string
import random
import time

router = APIRouter(prefix="/api/hr/jds", tags=["Job Descriptions"])


def generate_jd_unique_id() -> str:
    """Generate a unique JD ID in format: JD-XXXXXX"""
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"JD-{random_chars}"


class JDCreateRequest(BaseModel):
    title: str
    description_text: str
    client_name: Optional[str] = None
    budget_amount: Optional[float] = None  # In Indian Rupees
    your_earning: Optional[float] = None  # In Indian Rupees
    is_active: bool = True
    
    @field_validator('budget_amount')
    @classmethod
    def validate_budget_amount(cls, v):
        if v is not None:
            # Check if value exceeds 7 digits (9999999)
            if v > 9999999:
                raise ValueError('Budget amount cannot exceed 7 digits (99,99,999)')
        return v
    
    @field_validator('your_earning')
    @classmethod
    def validate_your_earning(cls, v):
        if v is not None:
            # Check if value exceeds 7 digits (9999999)
            if v > 9999999:
                raise ValueError('Earning amount cannot exceed 7 digits (99,99,999)')
        return v


class JDResponse(BaseModel):
    id: str
    jd_unique_id: Optional[str] = None
    title: str
    description_text: str
    parsed_jd: Optional[dict] = None
    uploaded_by: str
    created_at: datetime
    client_name: Optional[str] = None
    budget_amount: Optional[float] = None
    your_earning: Optional[float] = None
    is_active: bool = True
    status: str = "active"
    invoice_date: Optional[datetime] = None
    requirement_fulfilled: bool = False


class MatchResult(BaseModel):
    resume_id: str
    candidate_name: str
    score: float
    reasons: List[str]
    missing_skills: List[str]
    strengths: List[str]
    experience_match: str
    skill_match_percentage: float
    overall_fit: str
    detailed_scores: Dict[str, Any]


@router.post("/", response_model=JDResponse)
async def create_jd(
    jd_data: JDCreateRequest,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Create job description from text"""
    db = await get_db()
    
    try:
        # Parse JD with AI
        parsed_jd = await parse_job_description(jd_data.description_text)
        
        # Generate unique JD ID
        jd_unique_id = generate_jd_unique_id()
        
        # Check if ID already exists (very unlikely, but handle it)
        while await db.jds.find_one({"jd_unique_id": jd_unique_id}):
            jd_unique_id = generate_jd_unique_id()
        
        # Create JD document
        jd_doc = {
            "jd_unique_id": jd_unique_id,
            "title": jd_data.title,
            "description_text": jd_data.description_text,
            "parsed_jd": parsed_jd,
            "uploaded_by": str(current_user["_id"]),
            "client_name": jd_data.client_name,
            "budget_amount": jd_data.budget_amount,
            "your_earning": jd_data.your_earning,
            "is_active": jd_data.is_active,
            "status": "active" if jd_data.is_active else "inactive",
            "requirement_fulfilled": False,  # Default to not fulfilled
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.jds.insert_one(jd_doc)
        
        # Return created JD
        created_jd = await db.jds.find_one({"_id": result.inserted_id})
        return JDResponse(
            id=str(created_jd["_id"]),
            title=created_jd["title"],
            description_text=created_jd["description_text"],
            parsed_jd=created_jd.get("parsed_jd"),
            uploaded_by=created_jd["uploaded_by"],
            created_at=created_jd["created_at"],
            jd_unique_id=created_jd.get("jd_unique_id"),
            client_name=created_jd.get("client_name"),
            budget_amount=created_jd.get("budget_amount"),
            your_earning=created_jd.get("your_earning"),
            is_active=created_jd.get("is_active", True),
            status=created_jd.get("status", "active")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create JD: {str(e)}"
        )


@router.post("/upload", response_model=JDResponse)
async def upload_jd_file(
    title: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Upload JD from PDF/DOC file"""
    # Validate file type (reuse resume validation)
    validate_resume_file(file)
    
    try:
        # Save file temporarily
        temp_file_path = await save_upload_file_tmp(file)
        
        # Extract text
        loop = asyncio.get_event_loop()
        description_text = await loop.run_in_executor(None, extract_text_from_file, temp_file_path)
        
        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass
        
        if not description_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content found in file"
            )
        
        # Parse JD with AI
        parsed_jd = await parse_job_description(description_text)
        
        db = await get_db()
        
        # Generate unique JD ID
        jd_unique_id = generate_jd_unique_id()
        while await db.jds.find_one({"jd_unique_id": jd_unique_id}):
            jd_unique_id = generate_jd_unique_id()
        
        # Create JD document
        jd_doc = {
            "jd_unique_id": jd_unique_id,
            "title": title,
            "description_text": description_text,
            "parsed_jd": parsed_jd,
            "uploaded_by": str(current_user["_id"]),
            "is_active": True,  # Default to active for file uploads
            "status": "active",
            "requirement_fulfilled": False,  # Default to not fulfilled
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.jds.insert_one(jd_doc)
        
        # Return created JD
        created_jd = await db.jds.find_one({"_id": result.inserted_id})
        return JDResponse(
            id=str(created_jd["_id"]),
            title=created_jd["title"],
            description_text=created_jd["description_text"],
            parsed_jd=created_jd.get("parsed_jd"),
            uploaded_by=created_jd["uploaded_by"],
            created_at=created_jd["created_at"],
            jd_unique_id=created_jd.get("jd_unique_id"),
            client_name=created_jd.get("client_name"),
            budget_amount=created_jd.get("budget_amount"),
            your_earning=created_jd.get("your_earning"),
            is_active=created_jd.get("is_active", True),
            status=created_jd.get("status", "active")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload JD: {str(e)}"
        )


@router.get("/", response_model=List[JDResponse])
async def get_jds(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get all JDs for current HR"""
    db = await get_db()
    
    # Admins can see all JDs, HR users see only their own
    query: Dict[str, Any] = {}
    if current_user["role"] != "admin":
        query["uploaded_by"] = str(current_user["_id"])
    jds = await db.jds.find(query).sort("created_at", -1).to_list(None)
    
    return [
        JDResponse(
            id=str(jd["_id"]),
            jd_unique_id=jd.get("jd_unique_id"),
            title=jd["title"],
            description_text=jd["description_text"],
            parsed_jd=jd.get("parsed_jd"),
            uploaded_by=jd["uploaded_by"],
            created_at=jd["created_at"],
            client_name=jd.get("client_name"),
            budget_amount=jd.get("budget_amount"),
            your_earning=jd.get("your_earning"),
            is_active=jd.get("is_active", True),
            status=jd.get("status", "active"),
            invoice_date=jd.get("invoice_date"),
            requirement_fulfilled=jd.get("requirement_fulfilled", False)
        )
        for jd in jds
    ]


@router.get("/fulfilled", response_model=List[JDResponse])
async def get_fulfilled_jds(
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Get all fulfilled JDs for current HR (for invoice generation)"""
    db = await get_db()
    
    # Admins and accountants can see all fulfilled JDs, HR users see only their own
    query: Dict[str, Any] = {"requirement_fulfilled": True}
    if current_user["role"] not in ["admin", "accountant"]:
        query["uploaded_by"] = str(current_user["_id"])
    jds = await db.jds.find(query).sort("created_at", -1).to_list(None)
    
    return [
        JDResponse(
            id=str(jd["_id"]),
            jd_unique_id=jd.get("jd_unique_id"),
            title=jd["title"],
            description_text=jd["description_text"],
            parsed_jd=jd.get("parsed_jd"),
            uploaded_by=jd["uploaded_by"],
            created_at=jd["created_at"],
            client_name=jd.get("client_name"),
            budget_amount=jd.get("budget_amount"),
            your_earning=jd.get("your_earning"),
            is_active=jd.get("is_active", True),
            status=jd.get("status", "active"),
            invoice_date=jd.get("invoice_date"),
            requirement_fulfilled=jd.get("requirement_fulfilled", False)
        )
        for jd in jds
    ]


@router.get("/all-for-invoice", response_model=List[JDResponse])
async def get_all_jds_for_invoice(
    current_user: dict = Depends(require_roles(["hr", "admin", "accountant"]))
):
    """Get all JDs (not just fulfilled) for invoice generation - shows all JDs that can be invoiced"""
    db = await get_db()
    
    # Admins and accountants can see all JDs, HR users see only their own
    # Fetch all active JDs (not just fulfilled ones) so they appear in invoice section immediately
    query: Dict[str, Any] = {"is_active": True}
    if current_user["role"] not in ["admin", "accountant"]:
        query["uploaded_by"] = str(current_user["_id"])
    jds = await db.jds.find(query).sort("created_at", -1).to_list(None)
    
    return [
        JDResponse(
            id=str(jd["_id"]),
            jd_unique_id=jd.get("jd_unique_id"),
            title=jd["title"],
            description_text=jd["description_text"],
            parsed_jd=jd.get("parsed_jd"),
            uploaded_by=jd["uploaded_by"],
            created_at=jd["created_at"],
            client_name=jd.get("client_name"),
            budget_amount=jd.get("budget_amount"),
            your_earning=jd.get("your_earning"),
            is_active=jd.get("is_active", True),
            status=jd.get("status", "active"),
            invoice_date=jd.get("invoice_date"),
            requirement_fulfilled=jd.get("requirement_fulfilled", False)
        )
        for jd in jds
    ]


@router.get("/{jd_id}", response_model=JDResponse)
async def get_jd(
    jd_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get specific JD"""
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Admins can see any JD, HR users see only their own
    jd_query: Dict[str, Any] = {"_id": jd_object_id}
    if current_user["role"] != "admin":
        jd_query["uploaded_by"] = str(current_user["_id"])
    jd = await db.jds.find_one(jd_query)
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    return JDResponse(
        id=str(jd["_id"]),
        jd_unique_id=jd.get("jd_unique_id"),
        title=jd["title"],
        description_text=jd["description_text"],
        parsed_jd=jd.get("parsed_jd"),
        uploaded_by=jd["uploaded_by"],
        created_at=jd["created_at"],
        client_name=jd.get("client_name"),
        budget_amount=jd.get("budget_amount"),
        your_earning=jd.get("your_earning"),
        is_active=jd.get("is_active", True),
        status=jd.get("status", "active"),
        invoice_date=jd.get("invoice_date")
    )


class InvoiceDateUpdate(BaseModel):
    invoice_date: Optional[datetime] = None


class RequirementFulfilledUpdate(BaseModel):
    requirement_fulfilled: bool


@router.patch("/{jd_id}/requirement-fulfilled", response_model=JDResponse)
async def update_requirement_fulfilled(
    jd_id: str,
    fulfilled_data: RequirementFulfilledUpdate,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Update requirement fulfilled status for a JD"""
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Check if JD exists - Admins can see any JD, HR users see only their own
    jd_query: Dict[str, Any] = {"_id": jd_object_id}
    if current_user["role"] != "admin":
        jd_query["uploaded_by"] = str(current_user["_id"])
    jd = await db.jds.find_one(jd_query)
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    try:
        # Update requirement fulfilled status
        update_data = {
            "requirement_fulfilled": fulfilled_data.requirement_fulfilled,
            "updated_at": datetime.utcnow()
        }
        
        await db.jds.update_one(
            {"_id": jd_object_id},
            {"$set": update_data}
        )
        
        # Return updated JD
        updated_jd = await db.jds.find_one({"_id": jd_object_id})
        return JDResponse(
            id=str(updated_jd["_id"]),
            jd_unique_id=updated_jd.get("jd_unique_id"),
            title=updated_jd["title"],
            description_text=updated_jd["description_text"],
            parsed_jd=updated_jd.get("parsed_jd"),
            uploaded_by=updated_jd["uploaded_by"],
            created_at=updated_jd["created_at"],
            client_name=updated_jd.get("client_name"),
            budget_amount=updated_jd.get("budget_amount"),
            your_earning=updated_jd.get("your_earning"),
            is_active=updated_jd.get("is_active", True),
            status=updated_jd.get("status", "active"),
            invoice_date=updated_jd.get("invoice_date"),
            requirement_fulfilled=updated_jd.get("requirement_fulfilled", False)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update requirement fulfilled status: {str(e)}"
        )


@router.patch("/{jd_id}/invoice-date", response_model=JDResponse)
async def update_invoice_date(
    jd_id: str,
    invoice_data: InvoiceDateUpdate,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Update invoice date for a JD"""
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Check if JD exists - Admins can see any JD, HR users see only their own
    jd_query: Dict[str, Any] = {"_id": jd_object_id}
    if current_user["role"] != "admin":
        jd_query["uploaded_by"] = str(current_user["_id"])
    jd = await db.jds.find_one(jd_query)
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    try:
        # Update invoice date
        update_data = {
            "invoice_date": invoice_data.invoice_date,
            "updated_at": datetime.utcnow()
        }
        
        await db.jds.update_one(
            {"_id": jd_object_id},
            {"$set": update_data}
        )
        
        # Return updated JD
        updated_jd = await db.jds.find_one({"_id": jd_object_id})
        return JDResponse(
            id=str(updated_jd["_id"]),
            jd_unique_id=updated_jd.get("jd_unique_id"),
            title=updated_jd["title"],
            description_text=updated_jd["description_text"],
            parsed_jd=updated_jd.get("parsed_jd"),
            uploaded_by=updated_jd["uploaded_by"],
            created_at=updated_jd["created_at"],
            client_name=updated_jd.get("client_name"),
            budget_amount=updated_jd.get("budget_amount"),
            your_earning=updated_jd.get("your_earning"),
            is_active=updated_jd.get("is_active", True),
            status=updated_jd.get("status", "active"),
            invoice_date=updated_jd.get("invoice_date"),
            requirement_fulfilled=updated_jd.get("requirement_fulfilled", False)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update invoice date: {str(e)}"
        )


@router.patch("/{jd_id}", response_model=JDResponse)
async def update_jd(
    jd_id: str,
    jd_data: JDCreateRequest,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Update JD"""
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Check if JD exists - Admins can see any JD, HR users see only their own
    jd_query: Dict[str, Any] = {"_id": jd_object_id}
    if current_user["role"] != "admin":
        jd_query["uploaded_by"] = str(current_user["_id"])
    jd = await db.jds.find_one(jd_query)
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    try:
        # Re-parse JD with AI
        parsed_jd = await parse_job_description(jd_data.description_text)
        
        # Update JD
        update_data = {
            "title": jd_data.title,
            "description_text": jd_data.description_text,
            "parsed_jd": parsed_jd,
            "updated_at": datetime.utcnow()
        }
        
        await db.jds.update_one(
            {"_id": jd_object_id},
            {"$set": update_data}
        )
        
        # Return updated JD
        updated_jd = await db.jds.find_one({"_id": jd_object_id})
        return JDResponse(
            id=str(updated_jd["_id"]),
            jd_unique_id=updated_jd.get("jd_unique_id"),
            title=updated_jd["title"],
            description_text=updated_jd["description_text"],
            parsed_jd=updated_jd.get("parsed_jd"),
            uploaded_by=updated_jd["uploaded_by"],
            created_at=updated_jd["created_at"],
            client_name=updated_jd.get("client_name"),
            budget_amount=updated_jd.get("budget_amount"),
            your_earning=updated_jd.get("your_earning"),
            is_active=updated_jd.get("is_active", True),
            status=updated_jd.get("status", "active"),
            invoice_date=updated_jd.get("invoice_date")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update JD: {str(e)}"
        )


@router.delete("/{jd_id}")
async def delete_jd(
    jd_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Delete JD"""
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Admins can delete any JD, HR users can delete only their own
    delete_query: Dict[str, Any] = {"_id": jd_object_id}
    if current_user["role"] != "admin":
        delete_query["uploaded_by"] = str(current_user["_id"])
    result = await db.jds.delete_one(delete_query)
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    return {"message": "JD deleted successfully"}


@router.get("/{jd_id}/matches", response_model=List[MatchResult])
async def get_jd_matches(
    jd_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Get resumes that match the JD"""
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Get JD
    jd = await db.jds.find_one({
        "_id": jd_object_id,
        "uploaded_by": str(current_user["_id"])
    })
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    # Get all resumes - Admins can see all resumes, HR users see only their own
    resume_query: Dict[str, Any] = {}
    if current_user["role"] != "admin":
        resume_query["uploaded_by"] = str(current_user["_id"])
    resumes = await db.resumes.find(resume_query).to_list(None)
    
    if not resumes:
        return []
    
    # Prepare resume data for concurrent processing
    resume_data_list = []
    for resume in resumes:
        parsed_resume = await db.parsed_resumes.find_one({
            "resume_id": str(resume["_id"])
        })
        
        if parsed_resume:
            resume_data_list.append({
                "resume_id": str(resume["_id"]),
                "raw_text": parsed_resume.get("raw_text", ""),
                "parsed_resume": parsed_resume,
                "candidate_name": parsed_resume.get("candidate_name", "Unknown")
            })
    
    if not resume_data_list:
        return []
    
    # Process resumes with NER model + Sentence BERT
    import asyncio
    import time
    
    # Prepare resume-JD pairs for NER processing (include parsed JD, cached experience, and parsed resume data)
    resume_jd_pairs = []
    parsed_jd = jd.get("parsed_jd", {})
    
    for resume_data in resume_data_list:
        resume_text = resume_data.get("raw_text", "")
        parsed_resume = resume_data.get("parsed_resume", {})
        # Get cached experience from upload time (performance optimization)
        experience_cache = parsed_resume.get("experience_cache")
        if experience_cache:
            print(f"[JD MATCH] Using cached experience for resume {resume_data.get('resume_id')} (faster)")
        else:
            print(f"[JD MATCH] No cached experience for resume {resume_data.get('resume_id')} (will extract on-the-fly)")
        # Pass parsed_resume data for optimization (name/email/phone can be reused)
        resume_jd_pairs.append((resume_text, jd["description_text"], parsed_jd, experience_cache, parsed_resume))
    
    # Process all resumes with NER model + Sentence BERT
    print(f"Processing {len(resume_jd_pairs)} resumes with NER model + Sentence BERT...")
    print(f"[JD PARSE] Using parsed_jd: {parsed_jd}")
    start_time = time.time()
    
    score_results = await score_multiple_resumes_with_ner(resume_jd_pairs)
    
    elapsed_time = time.time() - start_time
    print(f"NER processing completed in {elapsed_time:.2f} seconds")
    
    # Convert results to MatchResult objects
    matches = []
    for i, (resume_data, score_result) in enumerate(zip(resume_data_list, score_results)):
        try:
            if score_result and isinstance(score_result, dict) and "score" in score_result:
                resume_id = resume_data.get("resume_id", "")
                candidate_name = resume_data.get("candidate_name", "Unknown")
                
                matches.append(MatchResult(
                    resume_id=resume_id,
                    candidate_name=candidate_name,
                    score=score_result.get("score", 0.0),
                    reasons=score_result.get("reasons", []),
                    missing_skills=score_result.get("missing_skills", []),
                    strengths=score_result.get("strengths", []),
                    experience_match=score_result.get("experience_match", "N/A"),
                    skill_match_percentage=score_result.get("skill_match_percentage", 0.0),
                    overall_fit=score_result.get("overall_fit", "N/A"),
                    detailed_scores=score_result.get("detailed_scores", {})
                ))
                
        except Exception as e:
            print(f"Error processing resume {resume_data.get('resume_id', 'unknown')}: {e}")
            continue
    
    # Sort by score descending
    matches.sort(key=lambda x: x.score, reverse=True)
    
    print(f"Successfully processed {len(matches)} resumes")
    return matches


class OptimizedMatchResponse(BaseModel):
    total_processed: int
    total_matches: int
    top_matches: List[MatchResult]
    showing: int
    processing_time_seconds: float


async def pre_filter_resumes_by_skills_experience(
    db,
    jd_skills: List[str],
    min_experience: float,
    user_id: str,
    role: str,
    max_candidates: int = 2000
) -> List[Dict[str, Any]]:
    """
    Pre-filter resumes based on skills and experience before expensive scoring.
    This dramatically reduces the number of resumes to process.
    """
    # Build base query
    base_query: Dict[str, Any] = {}
    if role != "admin":
        base_query["uploaded_by"] = user_id
    
    # Normalize skills to lowercase for matching
    jd_skills_lower = [skill.lower() for skill in jd_skills] if jd_skills else []
    
    # MongoDB aggregation pipeline for efficient filtering
    pipeline = [
        {"$match": base_query},
        {
            "$lookup": {
                "from": "parsed_resumes",
                "localField": "_id",
                "foreignField": "resume_id",
                "as": "parsed"
            }
        },
        {"$unwind": {"path": "$parsed", "preserveNullAndEmptyArrays": False}},
    ]
    
    # Add skill filtering if skills are provided
    if jd_skills_lower:
        pipeline.append({
            "$match": {
                "parsed.extracted_skills": {
                    "$elemMatch": {
                        "$regex": "|".join(jd_skills_lower),
                        "$options": "i"
                    }
                }
            }
        })
    
    # Add experience filtering if min_experience is provided
    if min_experience and min_experience > 0:
        pipeline.append({
            "$match": {
                "$or": [
                    {"parsed.experience_years": {"$gte": min_experience - 1}},  # Allow 1 year less
                    {"parsed.experience_years": {"$exists": False}},  # Include if not specified
                    {"parsed.experience_years": None}
                ]
            }
        })
    
    # Limit results to avoid processing too many
    pipeline.append({"$limit": max_candidates})
    
    # Project only needed fields
    pipeline.append({
        "$project": {
            "_id": 1,
            "filename": 1,
            "uploaded_by": 1,
            "parsed": 1
        }
    })
    
    try:
        resumes = await db.resumes.aggregate(pipeline).to_list(None)
        print(f"[PRE-FILTER] Filtered {len(resumes)} resumes from potential candidates")
        return resumes
    except Exception as e:
        print(f"[PRE-FILTER] Error in pre-filtering: {e}")
        # Fallback: return empty list, will use all resumes
        return []


def generate_detailed_reasons(score_result: Dict[str, Any], jd: Dict[str, Any]) -> List[str]:
    """
    Generate detailed reasons for why a resume matches or doesn't match.
    Helps users understand the scoring.
    """
    reasons = []
    
    score = score_result.get("score", 0)
    skill_match = score_result.get("skill_match_percentage", 0)
    missing_skills = score_result.get("missing_skills", [])
    experience_match = score_result.get("experience_match", "N/A")
    strengths = score_result.get("strengths", [])
    
    # High score reasons (80+)
    if score >= 80:
        reasons.append(f"Excellent match! {score:.1f}% overall compatibility")
        if skill_match >= 80:
            reasons.append(f"Strong skill alignment ({skill_match:.1f}% skills match)")
        if experience_match in ["excellent", "good"]:
            reasons.append("Experience level matches or exceeds requirements")
        if strengths:
            reasons.append(f"Key strengths: {', '.join(strengths[:3])}")
    
    # Good score reasons (60-79)
    elif score >= 60:
        reasons.append(f"Good match with {score:.1f}% compatibility")
        if skill_match >= 60:
            reasons.append(f"Decent skill match ({skill_match:.1f}%)")
        else:
            reasons.append(f"Skill match needs improvement ({skill_match:.1f}%)")
        if missing_skills:
            reasons.append(f"Missing some skills: {', '.join(missing_skills[:3])}")
        if experience_match == "low":
            reasons.append("Experience level slightly below requirement")
    
    # Moderate score reasons (40-59)
    elif score >= 40:
        reasons.append(f"Moderate match ({score:.1f}%) - needs improvement")
        if missing_skills:
            reasons.append(f"Missing critical skills: {', '.join(missing_skills[:5])}")
        if experience_match == "low":
            reasons.append("Experience level below requirement")
        if skill_match < 50:
            reasons.append(f"Low skill match ({skill_match:.1f}%)")
    
    # Low score reasons (<40)
    else:
        reasons.append(f"Low match ({score:.1f}%) - significant gaps")
        if missing_skills:
            reasons.append(f"Missing many required skills: {', '.join(missing_skills[:5])}")
        if experience_match == "low":
            reasons.append("Experience level significantly below requirement")
        if skill_match < 30:
            reasons.append(f"Very low skill alignment ({skill_match:.1f}%)")
    
    return reasons


@router.get("/{jd_id}/matches-optimized", response_model=OptimizedMatchResponse)
async def get_jd_matches_optimized(
    jd_id: str,
    top_n: int = Query(5, ge=1, le=100, description="Number of top matches to return"),
    min_score_threshold: float = Query(50.0, ge=0, le=100, description="Minimum score to include"),
    enable_pre_filter: bool = Query(True, description="Enable pre-filtering for performance"),
    max_candidates: int = Query(2000, ge=100, le=5000, description="Max candidates to score"),
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """
    Optimized matching endpoint for large resume databases (10,000+).
    
    Features:
    - Pre-filtering based on skills and experience (10-30x faster)
    - Top N results with descending order
    - Detailed reasons for match/mismatch
    - Minimum score threshold
    """
    start_time = time.time()
    db = await get_db()
    
    try:
        jd_object_id = ObjectId(jd_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JD ID"
        )
    
    # Get JD
    jd = await db.jds.find_one({
        "_id": jd_object_id,
        "uploaded_by": str(current_user["_id"])
    })
    
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found"
        )
    
    # Extract JD requirements for pre-filtering
    parsed_jd = jd.get("parsed_jd", {})
    jd_skills = parsed_jd.get("skills", [])
    min_experience = parsed_jd.get("min_experience", 0) or parsed_jd.get("experience_required", 0) or 0
    
    # If no skills in parsed_jd, try to extract from description
    if not jd_skills:
        jd_text_lower = jd.get("description_text", "").lower()
        # Simple skill extraction (can be improved)
        common_skills = ["python", "java", "javascript", "react", "node", "angular", "vue", 
                        "django", "flask", "spring", "sql", "mongodb", "aws", "docker", "kubernetes"]
        jd_skills = [skill for skill in common_skills if skill in jd_text_lower]
    
    print(f"[OPTIMIZED MATCH] JD Skills: {jd_skills[:10]}, Min Experience: {min_experience}")
    
    # Step 1: Pre-filter resumes (FAST - reduces 10,000 to ~500-2000)
    if enable_pre_filter and (jd_skills or min_experience > 0):
        print(f"[OPTIMIZED MATCH] Pre-filtering resumes...")
        filtered_resumes = await pre_filter_resumes_by_skills_experience(
            db, jd_skills, min_experience,
            str(current_user["_id"]), current_user["role"],
            max_candidates=max_candidates
        )
    else:
        # Fallback: Get all resumes (old way)
        print(f"[OPTIMIZED MATCH] Pre-filtering disabled, using all resumes...")
        resume_query: Dict[str, Any] = {}
        if current_user["role"] != "admin":
            resume_query["uploaded_by"] = str(current_user["_id"])
        filtered_resumes = await db.resumes.find(resume_query).limit(max_candidates).to_list(None)
    
    if not filtered_resumes:
        return OptimizedMatchResponse(
            total_processed=0,
            total_matches=0,
            top_matches=[],
            showing=0,
            processing_time_seconds=time.time() - start_time
        )
    
    print(f"[OPTIMIZED MATCH] Processing {len(filtered_resumes)} filtered resumes...")
    
    # Step 2: Prepare resume data for scoring
    resume_data_list = []
    for resume in filtered_resumes:
        resume_id = str(resume["_id"])
        parsed_resume = None
        
        # Try to get parsed resume data
        if "parsed" in resume and resume["parsed"]:
            parsed_resume = resume["parsed"][0] if isinstance(resume["parsed"], list) else resume["parsed"]
        else:
            parsed_resume = await db.parsed_resumes.find_one({"resume_id": resume_id})
        
        if parsed_resume:
            resume_data_list.append({
                "resume_id": resume_id,
                "raw_text": parsed_resume.get("raw_text", ""),
                "parsed_resume": parsed_resume,
                "candidate_name": parsed_resume.get("candidate_name", "Unknown")
            })
    
    if not resume_data_list:
        return OptimizedMatchResponse(
            total_processed=len(filtered_resumes),
            total_matches=0,
            top_matches=[],
            showing=0,
            processing_time_seconds=time.time() - start_time
        )
    
    # Step 3: Score resumes (batch processing)
    resume_jd_pairs = []
    for resume_data in resume_data_list:
        resume_text = resume_data.get("raw_text", "")
        parsed_resume = resume_data.get("parsed_resume", {})
        experience_cache = parsed_resume.get("experience_cache")
        resume_jd_pairs.append((
            resume_text, 
            jd["description_text"], 
            parsed_jd, 
            experience_cache, 
            parsed_resume
        ))
    
    print(f"[OPTIMIZED MATCH] Scoring {len(resume_jd_pairs)} resumes...")
    score_start = time.time()
    
    score_results = await score_multiple_resumes_with_ner(resume_jd_pairs)
    
    score_time = time.time() - score_start
    print(f"[OPTIMIZED MATCH] Scoring completed in {score_time:.2f} seconds")
    
    # Step 4: Convert to MatchResult with enhanced reasons
    matches = []
    for i, (resume_data, score_result) in enumerate(zip(resume_data_list, score_results)):
        try:
            if score_result and isinstance(score_result, dict) and "score" in score_result:
                score = score_result.get("score", 0.0)
                
                # Generate detailed reasons
                reasons = generate_detailed_reasons(score_result, jd)
                
                matches.append(MatchResult(
                    resume_id=resume_data.get("resume_id", ""),
                    candidate_name=resume_data.get("candidate_name", "Unknown"),
                    score=score,
                    reasons=reasons,
                    missing_skills=score_result.get("missing_skills", []),
                    strengths=score_result.get("strengths", []),
                    experience_match=score_result.get("experience_match", "N/A"),
                    skill_match_percentage=score_result.get("skill_match_percentage", 0.0),
                    overall_fit=score_result.get("overall_fit", "N/A"),
                    detailed_scores=score_result.get("detailed_scores", {})
                ))
        except Exception as e:
            print(f"[OPTIMIZED MATCH] Error processing resume {i}: {e}")
            continue
    
    # Step 5: Sort by score descending
    matches.sort(key=lambda x: x.score, reverse=True)
    
    # Step 6: Apply minimum threshold and limit
    filtered_matches = [m for m in matches if m.score >= min_score_threshold]
    top_matches = filtered_matches[:top_n]
    
    total_time = time.time() - start_time
    
    print(f"[OPTIMIZED MATCH] Successfully processed {len(resume_data_list)} resumes")
    print(f"[OPTIMIZED MATCH] Found {len(matches)} matches, showing top {len(top_matches)}")
    print(f"[OPTIMIZED MATCH] Total time: {total_time:.2f} seconds")
    
    return OptimizedMatchResponse(
        total_processed=len(resume_data_list),
        total_matches=len(matches),
        top_matches=top_matches,
        showing=len(top_matches),
        processing_time_seconds=total_time
    )
