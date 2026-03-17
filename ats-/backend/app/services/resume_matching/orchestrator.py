"""
Main Orchestrator Module
Coordinates the complete resume matching workflow from upload to suggestions.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
import uuid
from datetime import datetime

from .models import (
    ResumeData, JobDescription, SearchQuery, SearchResults,
    BulkProcessingJob, ProcessingStatus, FileType
)
from .parser import BulkResumeParser, parse_single_resume
from .jd_processor import JDProcessor
from .embedding_store import EmbeddingStore, AsyncEmbeddingStore
from .matcher import ResumeMatcher
from .resume_analysis import ResumeAnalysisService
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{settings.logs_dir}/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ResumeMatchingOrchestrator:
    """
    Main orchestrator that coordinates the complete resume matching workflow.
    Handles bulk processing, job description processing, matching, and GPT analysis.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all necessary components."""
        logger.info("Initializing Resume Matching Orchestrator")
        
        # Initialize components
        self.parser = BulkResumeParser(max_workers=settings.max_workers)
        self.jd_processor = JDProcessor()
        self.embedding_store = EmbeddingStore()
        self.async_embedding_store = AsyncEmbeddingStore(self.embedding_store)
        self.matcher = ResumeMatcher(self.embedding_store)
        self.analysis_service = ResumeAnalysisService()
        
        # State tracking
        self.processed_resumes: Dict[str, ResumeData] = {}
        self.processed_jds: Dict[str, JobDescription] = {}
        self.processing_jobs: Dict[str, BulkProcessingJob] = {}
        
        logger.info("Orchestrator initialized successfully")
    
    async def upload_and_process_resumes(
        self, 
        file_paths: List[Union[str, Path]],
        job_id: str = None
    ) -> BulkProcessingJob:
        """
        Upload and process multiple resume files.
        
        Args:
            file_paths: List of paths to resume files
            job_id: Optional job ID for tracking
            
        Returns:
            BulkProcessingJob with processing status
        """
        job_id = job_id or str(uuid.uuid4())
        
        # Create processing job
        processing_job = BulkProcessingJob(
            job_id=job_id,
            total_files=len(file_paths),
            status=ProcessingStatus.PROCESSING,
            started_at=datetime.utcnow()
        )
        
        self.processing_jobs[job_id] = processing_job
        
        logger.info(f"Starting bulk resume processing job {job_id} with {len(file_paths)} files")
        
        try:
            # Step 1: Parse resumes
            start_time = time.time()
            parsed_resumes = await self.parser.parse_resumes_async(file_paths)
            parse_time = time.time() - start_time
            
            # Update job status
            successful_resumes = [r for r in parsed_resumes if r.processing_status == ProcessingStatus.COMPLETED]
            failed_resumes = [r for r in parsed_resumes if r.processing_status == ProcessingStatus.FAILED]
            
            processing_job.processed_files = len(successful_resumes)
            processing_job.failed_files = len(failed_resumes)
            
            logger.info(f"Parsing completed: {len(successful_resumes)} successful, {len(failed_resumes)} failed")
            
            # Step 2: Generate and store embeddings
            if successful_resumes:
                start_time = time.time()
                await self.async_embedding_store.add_resumes_async(successful_resumes)
                embedding_time = time.time() - start_time
                
                # Store processed resumes
                for resume in successful_resumes:
                    resume_id = resume.id or resume.file_name
                    self.processed_resumes[resume_id] = resume
                
                logger.info(f"Embeddings generated and stored in {embedding_time:.2f}s")
            
            # Update job status
            processing_job.status = ProcessingStatus.COMPLETED
            processing_job.completed_at = datetime.utcnow()
            
            logger.info(f"Bulk processing job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in bulk processing job {job_id}: {e}")
            processing_job.status = ProcessingStatus.FAILED
            processing_job.errors.append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return processing_job
    
    async def process_job_description(
        self,
        description_text: str,
        title: str = None,
        company: str = None,
        jd_id: str = None
    ) -> JobDescription:
        """
        Process a job description and prepare it for matching.
        
        Args:
            description_text: Raw job description text
            title: Optional job title
            company: Optional company name
            jd_id: Optional JD ID
            
        Returns:
            Processed JobDescription object
        """
        jd_id = jd_id or str(uuid.uuid4())
        
        logger.info(f"Processing job description {jd_id}")
        
        try:
            # Process JD
            jd = self.jd_processor.process_job_description(
                description_text, title, company
            )
            jd.id = jd_id
            
            # Generate embedding
            jd_embedding = self.embedding_store.generator.generate_jd_embedding(jd)
            jd.embedding = jd_embedding.tolist()
            jd.embedding_model = self.embedding_store.generator.model_name
            
            # Store processed JD
            self.processed_jds[jd_id] = jd
            
            logger.info(f"Job description processed: {jd.title} at {jd.company or 'Unknown'}")
            
            return jd
            
        except Exception as e:
            logger.error(f"Error processing job description {jd_id}: {e}")
            raise
    
    async def find_matching_resumes(
        self,
        jd_id: str,
        top_k: int = 500,
        similarity_threshold: float = None,
        required_skills: List[str] = None,
        min_experience: float = None,
        max_experience: float = None,
        enable_gpt_analysis: bool = True,
        max_gpt_resumes: int = None
    ) -> SearchResults:
        """
        Find resumes matching a job description.
        
        Args:
            jd_id: Job description ID
            top_k: Number of top matches to return
            similarity_threshold: Minimum similarity threshold
            required_skills: Required skills filter
            min_experience: Minimum experience filter
            max_experience: Maximum experience filter
            enable_gpt_analysis: Whether to perform GPT analysis
            max_gpt_resumes: Maximum resumes for GPT analysis
            
        Returns:
            SearchResults with matched resumes
        """
        similarity_threshold = similarity_threshold or settings.similarity_threshold
        max_gpt_resumes = max_gpt_resumes or settings.max_resumes_for_gpt
        
        logger.info(f"Finding matches for JD {jd_id}")
        
        # Get job description
        jd = self.processed_jds.get(jd_id)
        if not jd:
            raise ValueError(f"Job description not found: {jd_id}")
        
        # Create search query
        query = SearchQuery(
            jd_id=jd_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            required_skills=required_skills or jd.required_skills,
            min_experience=min_experience or jd.min_experience,
            max_experience=max_experience or jd.max_experience,
            enable_gpt_analysis=enable_gpt_analysis,
            max_gpt_resumes=max_gpt_resumes
        )
        
        # Override matcher's JD retrieval method
        original_get_jd = self.matcher._get_job_description
        self.matcher._get_job_description = lambda x: self.processed_jds.get(x)
        
        try:
            # Perform matching
            start_time = time.time()
            search_results = self.matcher.search_matching_resumes(query)
            search_time = time.time() - start_time
            
            logger.info(f"Found {search_results.total_matches} matches in {search_time:.2f}s")
            
            # Perform Gemini analysis if enabled
            if enable_gpt_analysis and search_results.results:
                gemini_start_time = time.time()
                
                # Enhance with Gemini analysis
                enhanced_results = await self.analysis_service.enhance_match_results(
                    search_results.results,
                    self.processed_resumes,
                    jd,
                    max_gpt_resumes
                )
                
                gemini_time = (time.time() - gemini_start_time) * 1000
                search_results.results = enhanced_results
                search_results.gpt_analysis_time_ms = gemini_time
                
                logger.info(f"Gemini analysis completed in {gemini_time:.2f}ms")
            
            return search_results
            
        finally:
            # Restore original method
            self.matcher._get_job_description = original_get_jd
    
    async def complete_workflow(
        self,
        resume_files: List[Union[str, Path]],
        job_description_text: str,
        job_title: str = None,
        company_name: str = None,
        **matching_params
    ) -> Dict[str, Any]:
        """
        Execute the complete workflow from resume upload to GPT suggestions.
        
        Args:
            resume_files: List of resume file paths
            job_description_text: Job description text
            job_title: Optional job title
            company_name: Optional company name
            **matching_params: Additional matching parameters
            
        Returns:
            Complete workflow results
        """
        workflow_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting complete workflow {workflow_id}")
        
        try:
            # Step 1: Process resumes
            logger.info("Step 1: Processing resumes...")
            processing_job = await self.upload_and_process_resumes(resume_files)
            
            if processing_job.status != ProcessingStatus.COMPLETED:
                raise Exception(f"Resume processing failed: {processing_job.errors}")
            
            # Step 2: Process job description
            logger.info("Step 2: Processing job description...")
            jd = await self.process_job_description(
                job_description_text, job_title, company_name
            )
            
            # Step 3: Find matching resumes
            logger.info("Step 3: Finding matching resumes...")
            search_results = await self.find_matching_resumes(jd.id, **matching_params)
            
            # Step 4: Generate summary
            total_time = time.time() - start_time
            
            # Get analysis summary
            analysis_summary = self.analysis_service.get_analysis_summary(search_results.results)
            
            workflow_results = {
                'workflow_id': workflow_id,
                'processing_job': processing_job,
                'job_description': jd,
                'search_results': search_results,
                'analysis_summary': analysis_summary,
                'workflow_time_seconds': round(total_time, 2),
                'embedding_store_stats': self.embedding_store.get_stats(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Complete workflow {workflow_id} finished successfully in {total_time:.2f}s")
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"Error in complete workflow {workflow_id}: {e}")
            raise
    
    def get_processing_status(self, job_id: str) -> Optional[BulkProcessingJob]:
        """Get the status of a processing job."""
        return self.processing_jobs.get(job_id)
    
    def get_job_description(self, jd_id: str) -> Optional[JobDescription]:
        """Get a processed job description by ID."""
        return self.processed_jds.get(jd_id)
    
    def get_resume(self, resume_id: str) -> Optional[ResumeData]:
        """Get a processed resume by ID."""
        return self.processed_resumes.get(resume_id)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        return {
            'total_resumes_processed': len(self.processed_resumes),
            'total_jds_processed': len(self.processed_jds),
            'active_processing_jobs': len([
                job for job in self.processing_jobs.values()
                if job.status == ProcessingStatus.PROCESSING
            ]),
            'embedding_store_stats': self.embedding_store.get_stats(),
            'gemini_usage_stats': self.analysis_service.gemini_generator.get_usage_statistics()
        }


# Convenience functions for direct usage
async def process_resumes_and_match(
    resume_files: List[Union[str, Path]],
    job_description: str,
    job_title: str = None,
    company: str = None,
    top_k: int = 100,
    enable_gpt: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to process resumes and find matches.
    
    Args:
        resume_files: List of resume file paths
        job_description: Job description text
        job_title: Optional job title
        company: Optional company name
        top_k: Number of top matches to return
        enable_gpt: Whether to enable GPT analysis
        
    Returns:
        Complete results dictionary
    """
    orchestrator = ResumeMatchingOrchestrator()
    
    return await orchestrator.complete_workflow(
        resume_files=resume_files,
        job_description_text=job_description,
        job_title=job_title,
        company_name=company,
        top_k=top_k,
        enable_gpt_analysis=enable_gpt
    )


async def analyze_single_resume_against_jd(
    resume_file: Union[str, Path],
    job_description: str,
    job_title: str = None,
    company: str = None
) -> Dict[str, Any]:
    """
    Analyze a single resume against a job description.
    
    Args:
        resume_file: Path to resume file
        job_description: Job description text
        job_title: Optional job title
        company: Optional company name
        
    Returns:
        Analysis results
    """
    orchestrator = ResumeMatchingOrchestrator()
    
    # Process single resume
    resume_data = parse_single_resume(resume_file)
    orchestrator.processed_resumes[resume_data.file_name] = resume_data
    
    # Process JD
    jd = await orchestrator.process_job_description(job_description, job_title, company)
    
    # Perform Gemini analysis
    analysis = await orchestrator.analysis_service.analyze_resume_for_jd(resume_data, jd)
    
    return {
        'resume': resume_data,
        'job_description': jd,
        'gpt_analysis': analysis,
        'timestamp': datetime.utcnow().isoformat()
    }
