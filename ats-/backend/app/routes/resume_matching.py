"""
Resume Matching Routes
Provides AI-powered resume matching and analysis endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Query, UploadFile, File
from app.deps_rbac import require_roles
from app.services.resume_matching import (
    ResumeMatchingOrchestrator, 
    ResumeData, 
    JobDescription, 
    SearchQuery,
    SearchResults,
    BulkProcessingJob,
    ProcessingStatus
)
from app.services.resume_matching.orchestrator import process_resumes_and_match, analyze_single_resume_against_jd
from typing import List, Optional, Dict, Any
import tempfile
import os
from pathlib import Path
import uuid

router = APIRouter(prefix="/api/hr/resume-matching", tags=["Resume Matching"])

# Global orchestrator instance
orchestrator = ResumeMatchingOrchestrator()


@router.post("/process-resumes")
async def process_resumes_for_matching(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Process multiple resume files for AI matching"""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Save files temporarily
    temp_files = []
    try:
        for file in files:
            if not file.filename.lower().endswith(('.pdf', '.docx')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.filename}"
                )
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=Path(file.filename).suffix
            )
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_files.append(temp_file.name)
        
        # Process resumes in background
        job_id = str(uuid.uuid4())
        background_tasks.add_task(
            orchestrator.upload_and_process_resumes,
            temp_files,
            job_id
        )
        
        return {
            "message": "Resume processing started",
            "job_id": job_id,
            "total_files": len(files),
            "status": "processing"
        }
        
    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resumes: {str(e)}"
        )


@router.get("/processing-status/{job_id}")
async def get_processing_status(
    job_id: str,
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Get the status of a resume processing job"""
    job = orchestrator.get_processing_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found"
        )
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_files": job.total_files,
        "processed_files": job.processed_files,
        "failed_files": job.failed_files,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "errors": job.errors
    }


@router.post("/process-job-description")
async def process_job_description(
    job_description: str,
    title: Optional[str] = None,
    company: Optional[str] = None,
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Process a job description for matching"""
    try:
        jd = await orchestrator.process_job_description(
            job_description, title, company
        )
        
        return {
            "message": "Job description processed successfully",
            "jd_id": jd.id,
            "title": jd.title,
            "company": jd.company,
            "required_skills": jd.required_skills,
            "preferred_skills": jd.preferred_skills,
            "min_experience": jd.min_experience,
            "max_experience": jd.max_experience
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process job description: {str(e)}"
        )


@router.post("/find-matches/{jd_id}")
async def find_matching_resumes(
    jd_id: str,
    top_k: int = Query(100, ge=1, le=1000),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    enable_gpt_analysis: bool = Query(True),
    max_gpt_resumes: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Find resumes matching a job description"""
    try:
        search_results = await orchestrator.find_matching_resumes(
            jd_id=jd_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            enable_gpt_analysis=enable_gpt_analysis,
            max_gpt_resumes=max_gpt_resumes
        )
        
        # Convert results to response format
        matches = []
        for result in search_results.results:
            match_data = {
                "resume_id": result.resume_id,
                "similarity_score": result.similarity_score,
                "skills_match": result.skills_match,
                "experience_match": result.experience_match,
                "gpt_analysis": result.gpt_analysis.dict() if result.gpt_analysis else None
            }
            matches.append(match_data)
        
        return {
            "message": "Matching completed",
            "jd_id": jd_id,
            "total_matches": search_results.total_matches,
            "search_time_ms": search_results.search_time_ms,
            "gpt_analysis_time_ms": search_results.gpt_analysis_time_ms,
            "matches": matches
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find matches: {str(e)}"
        )


@router.post("/complete-workflow")
async def complete_matching_workflow(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    job_description: str = Query(...),
    job_title: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    top_k: int = Query(100, ge=1, le=1000),
    enable_gpt: bool = Query(True),
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Complete workflow: process resumes and find matches in one go"""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Save files temporarily
    temp_files = []
    try:
        for file in files:
            if not file.filename.lower().endswith(('.pdf', '.docx')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.filename}"
                )
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=Path(file.filename).suffix
            )
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_files.append(temp_file.name)
        
        # Run complete workflow
        workflow_id = str(uuid.uuid4())
        background_tasks.add_task(
            _run_complete_workflow,
            temp_files,
            job_description,
            job_title,
            company,
            top_k,
            enable_gpt,
            workflow_id
        )
        
        return {
            "message": "Complete workflow started",
            "workflow_id": workflow_id,
            "total_files": len(files),
            "status": "processing"
        }
        
    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


async def _run_complete_workflow(
    temp_files: List[str],
    job_description: str,
    job_title: Optional[str],
    company: Optional[str],
    top_k: int,
    enable_gpt: bool,
    workflow_id: str
):
    """Background task to run complete workflow"""
    try:
        results = await process_resumes_and_match(
            resume_files=temp_files,
            job_description=job_description,
            job_title=job_title,
            company=company,
            top_k=top_k,
            enable_gpt=enable_gpt
        )
        
        # Store results (you might want to save to database)
        # For now, we'll just log the results
        print(f"Workflow {workflow_id} completed successfully")
        print(f"Processed {results['processing_job'].processed_files} resumes")
        print(f"Found {results['search_results'].total_matches} matches")
        
    except Exception as e:
        print(f"Workflow {workflow_id} failed: {str(e)}")
    finally:
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass


@router.post("/analyze-single-resume")
async def analyze_single_resume(
    file: UploadFile = File(...),
    job_description: str = Query(...),
    job_title: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Analyze a single resume against a job description"""
    if not file.filename.lower().endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    
    # Save file temporarily
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=Path(file.filename).suffix
        )
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Analyze resume
        results = await analyze_single_resume_against_jd(
            resume_file=temp_file.name,
            job_description=job_description,
            job_title=job_title,
            company=company
        )
        
        return {
            "message": "Analysis completed",
            "resume": results['resume'].dict(),
            "job_description": results['job_description'].dict(),
            "gpt_analysis": results['gpt_analysis'].dict(),
            "timestamp": results['timestamp']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_file:
            try:
                os.unlink(temp_file.name)
            except:
                pass


@router.get("/system-stats")
async def get_system_statistics(
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Get system statistics"""
    try:
        stats = orchestrator.get_system_stats()
        return {
            "message": "System statistics retrieved",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/resume/{resume_id}")
async def get_resume_details(
    resume_id: str,
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Get details of a processed resume"""
    try:
        resume = orchestrator.get_resume(resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        return {
            "message": "Resume details retrieved",
            "resume": resume.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resume details: {str(e)}"
        )


@router.get("/job-description/{jd_id}")
async def get_job_description_details(
    jd_id: str,
    current_user: dict = Depends(require_roles(["hr"]))
):
    """Get details of a processed job description"""
    try:
        jd = orchestrator.get_job_description(jd_id)
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        return {
            "message": "Job description details retrieved",
            "job_description": jd.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job description details: {str(e)}"
        )
