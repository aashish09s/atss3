"""
Configuration module for the Resume Matching System.
Uses the main backend settings.
"""

import os
from pathlib import Path
from typing import Optional
from app.core.config import settings as backend_settings


class ResumeMatchingSettings:
    """Application settings using backend configuration."""
    
    # Database Configuration
    mongodb_url: str = backend_settings.mongodb_uri
    database_name: str = "resume_matching_db"
    
    # Analysis Configuration (No AI dependencies)
    analysis_method: str = "rule_based"  # Using rule-based analysis instead of AI
    
    # FAISS Configuration
    faiss_index_path: str = backend_settings.resume_matching_faiss_index_path
    embeddings_model: str = backend_settings.resume_matching_embeddings_model
    
    # Processing Configuration
    max_workers: int = backend_settings.resume_matching_max_workers
    batch_size: int = backend_settings.resume_matching_batch_size
    max_resumes_for_analysis: int = backend_settings.resume_matching_max_resumes_for_analysis
    similarity_threshold: float = backend_settings.resume_matching_similarity_threshold
    
    # File Storage
    upload_dir: str = backend_settings.resume_matching_upload_dir
    processed_dir: str = backend_settings.resume_matching_processed_dir
    logs_dir: str = backend_settings.resume_matching_logs_dir
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = backend_settings.debug


def get_resume_matching_settings() -> ResumeMatchingSettings:
    """Get application settings instance."""
    return ResumeMatchingSettings()


def ensure_directories(settings: ResumeMatchingSettings) -> None:
    """Ensure all required directories exist."""
    directories = [
        settings.upload_dir,
        settings.processed_dir,
        settings.logs_dir,
        Path(settings.faiss_index_path).parent,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = get_resume_matching_settings()
ensure_directories(settings)
