import os
import aiofiles
from typing import Optional, Union
from app.core.config import settings
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import uuid
import tempfile
import shutil


class StorageService:
    def __init__(self):
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
    
    async def save_file(self, file_input: Union[str, object], filename: str) -> str:
        """Save file to storage (S3 or local) and return URL
        
        Args:
            file_input: Either a file path (str) or a file object (UploadFile.file or SpooledTemporaryFile)
            filename: Name for the saved file (can include path structure)
        """
        # Generate unique filename while preserving path structure
        if '/' in filename:
            # If filename contains path, extract the actual filename and add UUID
            path_parts = filename.split('/')
            actual_filename = path_parts[-1]
            path_structure = '/'.join(path_parts[:-1])
            unique_filename = f"{path_structure}/{uuid.uuid4()}_{actual_filename}"
        else:
            # Simple filename, just add UUID
            unique_filename = f"{uuid.uuid4()}_{filename}"
        
        if isinstance(file_input, str):
            # File path provided
            if self.s3_client and settings.aws_s3_bucket:
                return await self._save_to_s3(file_input, unique_filename)
            else:
                return await self._save_to_local(file_input, unique_filename)
        else:
            # File object provided (UploadFile.file or SpooledTemporaryFile)
            return await self._save_file_object(file_input, unique_filename)
    
    async def _save_to_s3(self, file_path: str, filename: str) -> str:
        """Save file to AWS S3"""
        try:
            with open(file_path, 'rb') as file:
                self.s3_client.upload_fileobj(
                    file,
                    settings.aws_s3_bucket,
                    f"resumes/{filename}"
                )
            
            # Return S3 URL
            return f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/resumes/{filename}"
            
        except (NoCredentialsError, ClientError) as e:
            # Fallback to local storage
            return await self._save_to_local(file_path, filename)
    
    async def _save_to_local(self, file_path: str, filename: str) -> str:
        """Save file to local storage"""
        # Make upload directory absolute
        upload_dir = os.path.abspath(settings.local_upload_dir)
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        # Handle nested directory structure
        dest_path = os.path.join(upload_dir, filename)
        dest_dir = os.path.dirname(dest_path)
        
        # Create nested directories if they don't exist
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        # Copy file to destination
        async with aiofiles.open(file_path, 'rb') as src:
            async with aiofiles.open(dest_path, 'wb') as dst:
                while True:
                    chunk = await src.read(8192)
                    if not chunk:
                        break
                    await dst.write(chunk)
        
        # Return full local URL
        return f"{settings.backend_base_url}/uploads/{filename}"
    
    async def _save_file_object(self, file_obj, filename: str) -> str:
        """Save file object to local storage and return URL"""
        # Make upload directory absolute
        upload_dir = os.path.abspath(settings.local_upload_dir)
        print(f"Storage service: local_upload_dir = {settings.local_upload_dir}")
        print(f"Storage service: absolute upload_dir = {upload_dir}")
        print(f"Storage service: filename = {filename}")
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        # Handle nested directory structure
        dest_path = os.path.join(upload_dir, filename)
        dest_dir = os.path.dirname(dest_path)
        
        print(f"Storage service: dest_path = {dest_path}")
        print(f"Storage service: dest_dir = {dest_dir}")
        
        # Create nested directories if they don't exist
        if dest_dir and not os.path.exists(dest_dir):
            print(f"Storage service: Creating directory {dest_dir}")
            os.makedirs(dest_dir, exist_ok=True)
        
        # Save the file object to destination
        try:
            # Reset file pointer to beginning if seek method exists
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            # Copy file content
            with open(dest_path, 'wb') as dst:
                shutil.copyfileobj(file_obj, dst)
            
            print(f"Storage service: File saved successfully to {dest_path}")
            
            # Return full local URL
            return f"{settings.backend_base_url}/uploads/{filename}"
            
        except Exception as e:
            print(f"Storage service: Error saving file: {e}")
            # Clean up on error
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise e
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from storage"""
        if file_url.startswith("https://") and "s3" in file_url:
            return await self._delete_from_s3(file_url)
        else:
            return await self._delete_from_local(file_url)
    
    async def _delete_from_s3(self, file_url: str) -> bool:
        """Delete file from S3"""
        try:
            # Extract key from URL
            key = file_url.split(f"{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/")[1]
            self.s3_client.delete_object(Bucket=settings.aws_s3_bucket, Key=key)
            return True
        except Exception:
            return False
    
    async def _delete_from_local(self, file_url: str) -> bool:
        """Delete file from local storage"""
        try:
            # Extract filename from URL (handle both full URLs and relative paths)
            if file_url.startswith(settings.backend_base_url):
                filename = file_url.split(f"{settings.backend_base_url}/uploads/")[1]
            else:
                filename = file_url.split("/uploads/")[1]
            
            file_path = os.path.join(settings.local_upload_dir, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False


# Global storage service instance
storage_service = StorageService()
