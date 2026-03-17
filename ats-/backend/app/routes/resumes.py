from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks, Query
from app.db.mongo import get_db
from app.deps_rbac import require_roles
from app.utils.file_utils import validate_resume_file, save_upload_file_tmp, extract_zip_and_filter
from app.services.storage import storage_service
from app.services.parse_store import parse_and_store
from app.schemas.resume import ResumeOut
from app.core.config import settings
from bson import ObjectId
from typing import List, Optional, Dict, Any
import tempfile
import os
import hashlib

router = APIRouter(prefix="/api/hr/resumes", tags=["Resume Upload"])


@router.post("/upload")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Upload single resume file with duplicate checking"""
    # Validate file
    validate_resume_file(file)
    
    try:
        # Save file temporarily
        temp_file_path = await save_upload_file_tmp(file)
        
        # Save to storage (S3 or local)
        file_url = await storage_service.save_file(temp_file_path, file.filename)
        
        # Check for duplicates before processing
        from app.services.duplicate_checker import check_resume_duplicates
        from app.utils.file_utils import extract_text_from_file
        
        # Extract text content for duplicate checking
        text_content = await extract_text_from_file(temp_file_path)
        
        # Minimal fields for duplicate check only (no full parsing)
        from app.services.parse_store import get_duplicate_check_fields
        parsed_data = get_duplicate_check_fields(text_content)
        
        # Check for duplicates
        db = await get_db()
        duplicates = await check_resume_duplicates(db, parsed_data, text_content)
        
        if duplicates:
            # Return duplicate information instead of processing
            return {
                "message": "Duplicate resume detected",
                "filename": file.filename,
                "file_url": file_url,
                "duplicates_found": True,
                "duplicates": duplicates,
                "candidate_name": parsed_data.get("name", "Unknown"),
                "candidate_email": parsed_data.get("email", ""),
                "candidate_phone": parsed_data.get("phone", "")
            }
        
        # No duplicates found, proceed with normal processing
        background_tasks.add_task(
            parse_and_store,
            temp_file_path,
            str(current_user["_id"]),
            file.filename,
            file_url
        )
        
        return {
            "message": "Resume uploaded successfully. Processing in background.",
            "filename": file.filename,
            "file_url": file_url,
            "duplicates_found": False
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {str(e)}"
        )


@router.post("/bulk-upload")
async def bulk_upload_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Upload multiple resume files with duplicate checking"""
    results = []
    errors = []
    duplicates_found = []
    
    # Import duplicate checking functions
    from app.services.duplicate_checker import check_resume_duplicates
    from app.utils.file_utils import extract_text_from_file
    from app.services.parse_store import get_duplicate_check_fields

    db = await get_db()
    
    print(f"[BULK UPLOAD] Starting bulk upload for {len(files)} files")
    
    # Track files being processed in this batch to prevent duplicate queuing
    processed_file_signatures = set()
    
    for idx, file in enumerate(files, 1):
        temp_file_path = None
        try:
            print(f"[BULK UPLOAD] Processing file {idx}/{len(files)}: {file.filename}")
            
            # Validate each file
            validate_resume_file(file)
            
            # Save file temporarily
            temp_file_path = await save_upload_file_tmp(file)
            
            # Save to storage (S3 or local)
            file_url = await storage_service.save_file(temp_file_path, file.filename)
            
            # Check for duplicates before processing
            text_content = await extract_text_from_file(temp_file_path)
            parsed_data = get_duplicate_check_fields(text_content)
            duplicates = await check_resume_duplicates(db, parsed_data, text_content)
            
            # Create a unique signature for this file (filename + user + content hash)
            # This prevents the same file from being queued twice in a single batch
            file_signature = hashlib.md5(f"{file.filename}|{current_user['_id']}|{text_content[:500]}".encode()).hexdigest()
            
            if duplicates:
                # Add to duplicates list instead of processing
                duplicates_found.append({
                    "filename": file.filename,
                    "file_url": file_url,
                    "candidate_name": parsed_data.get("name", "Unknown"),
                    "candidate_email": parsed_data.get("email", ""),
                    "candidate_phone": parsed_data.get("phone", ""),
                    "duplicates": duplicates
                })
                print(f"[BULK UPLOAD] Duplicate found for {file.filename}")
            elif file_signature in processed_file_signatures:
                # This exact file was already processed in this batch (prevent double-queuing)
                print(f"[BULK UPLOAD] File {file.filename} already queued in this batch, skipping duplicate")
                errors.append({
                    "filename": file.filename,
                    "error": "Duplicate file in upload batch"
                })
            else:
                # No duplicates found, proceed with normal processing
                processed_file_signatures.add(file_signature)
                background_tasks.add_task(
                    parse_and_store,
                    temp_file_path,
                    str(current_user["_id"]),
                    file.filename,
                    file_url
                )
                
                results.append({
                    "filename": file.filename,
                    "file_url": file_url,
                    "status": "queued_for_processing"
                })
                print(f"[BULK UPLOAD] Queued {file.filename} for processing")
            
        except Exception as e:
            error_msg = str(e)
            print(f"[BULK UPLOAD] Error processing {file.filename}: {error_msg}")
            errors.append({
                "filename": file.filename,
                "error": error_msg
            })
            # Clean up temp file if it exists
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    print(f"[BULK UPLOAD] Completed: {len(results)} successful, {len(errors)} failed, {len(duplicates_found)} duplicates")
    
    return {
        "message": f"Processed {len(results)} files successfully, {len(errors)} failed, {len(duplicates_found)} duplicates found",
        "successful_uploads": results,
        "errors": errors,
        "duplicates_found": duplicates_found,
        "has_duplicates": len(duplicates_found) > 0,
        "total_files": len(files),
        "processed_count": len(results) + len(errors) + len(duplicates_found)
    }


@router.get("/find-duplicates")
async def find_existing_duplicates(
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Find existing duplicate resumes in the database"""
    try:
        from app.services.duplicate_checker import DuplicateResumeChecker
        
        db = await get_db()
        checker = DuplicateResumeChecker(db)
        
        # Get all resumes - Admins can see all, HR users see only their own
        resume_query: Dict[str, Any] = {}
        if current_user["role"] != "admin":
            resume_query["uploaded_by"] = str(current_user["_id"])
        all_resumes = await db.resumes.find(resume_query).to_list(None)
        
        duplicate_groups = []
        processed_resumes = set()
        
        for resume in all_resumes:
            if str(resume["_id"]) in processed_resumes:
                continue
                
            parsed_data = resume.get("parsed_data", {})
            if not parsed_data.get("name") and not parsed_data.get("email") and not parsed_data.get("phone"):
                continue
                
            # Find duplicates for this resume
            duplicates = await checker.check_duplicate_by_parsed_data(parsed_data)
            
            if len(duplicates) > 1:  # More than 1 means there are duplicates
                # Add the current resume to the duplicates list
                current_resume_info = {
                    "resume_id": str(resume["_id"]),
                    "filename": resume.get("filename", ""),
                    "candidate_name": parsed_data.get("name", "Unknown"),
                    "candidate_email": parsed_data.get("email", ""),
                    "candidate_phone": parsed_data.get("phone", ""),
                    "uploaded_at": resume.get("created_at"),
                    "uploaded_by": resume.get("uploaded_by"),
                    "match_reasons": ["self"],
                    "status": resume.get("status", "submission")
                }
                
                all_duplicates = [current_resume_info] + duplicates
                duplicate_groups.append({
                    "group_id": str(resume["_id"]),
                    "candidate_name": parsed_data.get("name", "Unknown"),
                    "candidate_email": parsed_data.get("email", ""),
                    "candidate_phone": parsed_data.get("phone", ""),
                    "duplicates": all_duplicates,
                    "count": len(all_duplicates)
                })
                
                # Mark all duplicates as processed
                for dup in duplicates:
                    processed_resumes.add(dup["resume_id"])
                processed_resumes.add(str(resume["_id"]))
        
        return {
            "message": f"Found {len(duplicate_groups)} duplicate groups",
            "duplicate_groups": duplicate_groups,
            "total_duplicates": sum(group["count"] for group in duplicate_groups)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find duplicates: {str(e)}"
        )


@router.delete("/remove-duplicates")
async def remove_duplicate_resumes(
    request: dict,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Remove duplicate resumes from database"""
    try:
        from app.services.duplicate_checker import remove_duplicate_resumes
        
        # Extract duplicate_ids from request body
        duplicate_ids = request.get("duplicate_ids", [])
        if not duplicate_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No duplicate IDs provided"
            )
        
        db = await get_db()
        result = await remove_duplicate_resumes(db, duplicate_ids)
        
        if result["success"]:
            return {
                "message": f"Successfully removed {result['deleted_count']} duplicate resumes",
                "deleted_count": result["deleted_count"],
                "deleted_ids": result["deleted_ids"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove duplicates: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove duplicates: {str(e)}"
        )


@router.post("/bulk-upload-zip")
async def bulk_upload_from_zip(
    background_tasks: BackgroundTasks,
    zip_file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Upload resumes from ZIP file"""
    if not zip_file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are allowed"
        )
    
    try:
        # Save ZIP file temporarily
        temp_zip_path = await save_upload_file_tmp(zip_file)
        
        # Extract resume files from ZIP
        extracted_files = extract_zip_and_filter(temp_zip_path)
        
        results = []
        errors = []
        
        for file_path in extracted_files:
            try:
                filename = os.path.basename(file_path)
                
                # Save to storage
                file_url = await storage_service.save_file(file_path, filename)
                
                # Schedule background parsing
                background_tasks.add_task(
                    parse_and_store,
                    file_path,
                    str(current_user["_id"]),
                    filename,
                    file_url
                )
                
                results.append({
                    "filename": filename,
                    "file_url": file_url,
                    "status": "queued_for_processing"
                })
                
            except Exception as e:
                errors.append({
                    "filename": os.path.basename(file_path),
                    "error": str(e)
                })
        
        # Clean up ZIP file
        try:
            os.unlink(temp_zip_path)
        except Exception:
            pass
        
        return {
            "message": f"Extracted and processed {len(results)} files, {len(errors)} failed",
            "successful_uploads": results,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ZIP file: {str(e)}"
        )


@router.get("/", response_model=List[ResumeOut])
async def get_resumes(
    current_user: dict = Depends(require_roles(["hr", "admin"])),
    search: Optional[str] = Query(None, description="Search by candidate name or skills"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(50, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get resumes with search and filtering"""
    db = await get_db()
    
    # Build search query - Admins can see all resumes, HR users see only their own
    query: Dict[str, Any] = {}
    if current_user["role"] != "admin":
        query["uploaded_by"] = str(current_user["_id"])
    
    if status_filter:
        query["status"] = status_filter
    
    # Text search in parsed data
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"parsed_data.name": search_regex},
            {"parsed_data.skills": {"$elemMatch": search_regex}},
            {"filename": search_regex}
        ]
    
    # Execute query with pagination
    resumes = await db.resumes.find(query)\
        .sort("created_at", -1)\
        .skip(offset)\
        .limit(limit)\
        .to_list(None)
    
    return [
        ResumeOut(
            id=str(resume["_id"]),
            filename=resume["filename"],
            file_url=resume["file_url"],
            download_url=f"{settings.backend_base_url}/api/hr/resume/download/{resume['_id']}",
            uploaded_by=resume["uploaded_by"],
            status=resume["status"],
            parsed_data=resume.get("parsed_data"),
            ats_score=resume.get("ats_score"),
            shared_with_manager=resume.get("shared_with_manager", False),
            created_at=resume["created_at"]
        )
        for resume in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin", "manager"]))
):
    """Get specific resume details"""
    db = await get_db()
    user_id_str = str(current_user["_id"]) if current_user.get("_id") is not None else "unknown"
    
    # Clean resume_id - remove any trailing colons or other characters
    original_resume_id = resume_id
    resume_id = resume_id.strip().split(':')[0] if ':' in resume_id else resume_id.strip()
    
    print(f"[GET RESUME] Request for resume_id: '{original_resume_id}' (cleaned: '{resume_id}') by user: {current_user.get('email', current_user.get('_id'))}")
    
    try:
        resume_object_id = ObjectId(resume_id)
    except Exception as e:
        print(f"[GET RESUME] Invalid resume ID format: {resume_id}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resume ID format: {resume_id}"
        )
    
    # Access control: Admins can see all, HR users see only their own, Managers see shared resumes
    resume_query: Dict[str, Any] = {"_id": resume_object_id}
    if current_user["role"] == "admin":
        # Admins can see all resumes - no additional filter needed
        pass
    elif current_user["role"] == "manager":
        # Managers can see resumes shared with them (from their HR team)
        hr_users = await db.users.find({
            "manager_id": str(current_user["_id"]),
            "role": "hr"
        }).to_list(None)
        
        hr_user_ids = [str(hr["_id"]) for hr in hr_users]
        
        resume_query["$or"] = [
            {"uploaded_by": {"$in": hr_user_ids}, "shared_with_manager": True}
        ]
    else:  # hr
        resume_query["uploaded_by"] = str(current_user["_id"])
    
    resume = await db.resumes.find_one(resume_query)
    
    # If not found with ownership, check if it exists at all (for better error message)
    if not resume:
        resume_exists = await db.resumes.find_one({"_id": resume_object_id})
        if not resume_exists:
            resume_exists = await db.resumes.find_one({"_id": resume_id})
        if resume_exists:
            actual_owner = resume_exists.get("uploaded_by", "unknown")
            print(f"[GET RESUME] Resume {resume_id} exists but owned by {actual_owner}, not {user_id_str}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this resume"
            )
        else:
            print(f"[GET RESUME] Resume {resume_id} not found in database at all")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )
    
    print(f"[GET RESUME] Successfully found resume {resume_id}")
    
    return ResumeOut(
        id=str(resume["_id"]),
        filename=resume["filename"],
        file_url=resume["file_url"],
        download_url=f"{settings.backend_base_url}/api/hr/resume/download/{resume['_id']}",
        uploaded_by=resume["uploaded_by"],
        status=resume["status"],
        parsed_data=resume.get("parsed_data"),
        ats_score=resume.get("ats_score"),
        shared_with_manager=resume.get("shared_with_manager", False),
        created_at=resume["created_at"]
    )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(require_roles(["hr", "admin"]))
):
    """Delete resume"""
    db = await get_db()
    
    try:
        resume_object_id = ObjectId(resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID"
        )
    
    # Get resume - Admins can see any resume, HR users see only their own
    resume_query: Dict[str, Any] = {"_id": resume_object_id}
    if current_user["role"] != "admin":
        resume_query["uploaded_by"] = str(current_user["_id"])
    resume = await db.resumes.find_one(resume_query)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Delete file from storage
    await storage_service.delete_file(resume["file_url"])
    
    # Delete from database
    await db.resumes.delete_one({"_id": resume_object_id})
    await db.parsed_resumes.delete_one({"resume_id": resume_id})
    
    return {"message": "Resume deleted successfully"}
