from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    
    # JWT
    jwt_secret_key: str
    jwt_refresh_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    refresh_token_expire_days: int = 7
    
    # Gemini AI
    gemini_api_key: Optional[str] = None
    
    # Ollama AI (Local Model) - Optimized for phi3:mini
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "qwen2.5:1.5b"
    ollama_enabled: bool = False  # Disabled to prevent timeout issues, use enhanced fallback
    ollama_timeout: int = 5  # 5 second timeout to prevent background processing
    ollama_max_tokens: int = 50  # Minimal tokens for JSON response only
    ollama_temperature: float = 0.0  # No randomness for consistency
    ollama_top_p: float = 0.3  # Lower for faster generation
    
    # Email SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = "SynHireOne"
    
    # Microsoft 365 OAuth 2.0 (Alternative to SMTP)
    use_microsoft365: bool = False
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_tenant_id: Optional[str] = None
    microsoft_sender_email: Optional[str] = None
    
    # WhatsApp Business API
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_api_version: str = "v18.0"
    whatsapp_enabled: bool = False
    
    # AWS S3 (Optional)
    use_s3: bool = False
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # Local Storage
    local_upload_dir: str = "./uploads"
    backend_base_url: Optional[str] = None
    frontend_base_url: Optional[str] = None
    frontend_url: str = "http://localhost:3000"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set defaults based on environment
        if not self.backend_base_url:
            if self.environment == "production":
                self.backend_base_url = "https://ats.trihdiconsulting.com"
            else:
                self.backend_base_url = "http://localhost:8000"
        
        if not self.frontend_base_url:
            if self.environment == "production":
                self.frontend_base_url = "https://ats.trihdiconsulting.com"
            else:
                self.frontend_base_url = "http://localhost:3000"
        self._validate_email_config()
    
    # Encryption
    encryption_key: Optional[str] = None
    
    # spaCy
    spacy_model: str = "en_core_web_sm"
    
    # Resume Matching System (No AI dependencies)
    resume_matching_faiss_index_path: str = "./data/faiss_index"
    resume_matching_embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    resume_matching_max_workers: int = 4
    resume_matching_batch_size: int = 100
    resume_matching_max_resumes_for_analysis: int = 100
    resume_matching_similarity_threshold: float = 0.7
    resume_matching_upload_dir: str = "./uploads"
    resume_matching_processed_dir: str = "./processed"
    resume_matching_logs_dir: str = "./logs"
    
    # App
    debug: bool = False
    environment: str = "development" 
    secret_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables
    
    def _validate_email_config(self):
        """Validate that either SMTP or Microsoft 365 is properly configured"""
        if self.use_microsoft365:
            # When using Microsoft 365, validate required fields
            if not all([self.microsoft_client_id, self.microsoft_client_secret, 
                       self.microsoft_tenant_id, self.microsoft_sender_email]):
                missing = []
                if not self.microsoft_client_id:
                    missing.append("microsoft_client_id")
                if not self.microsoft_client_secret:
                    missing.append("microsoft_client_secret")
                if not self.microsoft_tenant_id:
                    missing.append("microsoft_tenant_id")
                if not self.microsoft_sender_email:
                    missing.append("microsoft_sender_email")
                
                raise ValueError(
                    f"When use_microsoft365=true, these fields are required: {', '.join(missing)}"
                )
        else:
            # When using SMTP, validate required fields
            if not all([self.smtp_host, self.smtp_username, 
                       self.smtp_password, self.smtp_from_email]):
                missing = []
                if not self.smtp_host:
                    missing.append("smtp_host")
                if not self.smtp_username:
                    missing.append("smtp_username")
                if not self.smtp_password:
                    missing.append("smtp_password")
                if not self.smtp_from_email:
                    missing.append("smtp_from_email")
                
                raise ValueError(
                    f"When use_microsoft365=false, these SMTP fields are required: {', '.join(missing)}"
                )


settings = Settings()

# Debug: Print all environment variables and settings
print("DEBUG: Environment variables:")
import os
for key, value in os.environ.items():
    if 'key' in key.lower() or 'encrypt' in key.lower():
        print(f"  {key} = {value}")

print("DEBUG: Settings values:")
print(f"  encryption_key = {settings.encryption_key}")
print(f"  environment = {settings.environment}")
print(f"  debug = {settings.debug}")
