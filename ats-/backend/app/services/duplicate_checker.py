"""
Duplicate Resume Checker Service
Checks for duplicate resumes based on name, email, and phone number
"""

from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId
from datetime import datetime, timezone
import re


class DuplicateResumeChecker:
    """Service to check for duplicate resumes based on candidate information"""
    
    def __init__(self, db):
        self.db = db
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, remove extra spaces)"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip().lower())
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison"""
        if not phone:
            return ""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Return last 10 digits (assuming most phone numbers are 10 digits)
        return digits_only[-10:] if len(digits_only) >= 10 else digits_only
    
    def normalize_email(self, email: str) -> str:
        """Normalize email for comparison"""
        if not email:
            return ""
        return email.strip().lower()
    
    async def check_duplicate_by_parsed_data(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for duplicates based on parsed resume data
        Returns list of duplicate resumes found
        """
        try:
            name = parsed_data.get("name", "").strip()
            email = parsed_data.get("email", "").strip()
            phone = parsed_data.get("phone", "").strip()
            
            if not name and not email and not phone:
                return []
            
            # Build query for potential duplicates
            query_conditions = []
            
            # Check by name (exact match)
            if name:
                normalized_name = self.normalize_text(name)
                query_conditions.append({
                    "parsed_data.name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}
                })
            
            # Check by email (exact match)
            if email:
                normalized_email = self.normalize_email(email)
                query_conditions.append({
                    "parsed_data.email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}
                })
            
            # Check by phone (normalized match)
            if phone:
                normalized_phone = self.normalize_phone(phone)
                if normalized_phone:
                    # Find resumes with similar phone numbers
                    phone_patterns = [
                        {"parsed_data.phone": {"$regex": f".*{normalized_phone[-10:]}.*"}},
                        {"parsed_data.phone": {"$regex": f".*{normalized_phone}.*"}}
                    ]
                    query_conditions.extend(phone_patterns)
            
            if not query_conditions:
                return []
            
            # Find potential duplicates
            potential_duplicates = await self.db.resumes.find({
                "$or": query_conditions
            }).to_list(None)
            
            # Filter for actual duplicates
            duplicates = []
            for resume in potential_duplicates:
                resume_parsed = resume.get("parsed_data", {})
                resume_name = resume_parsed.get("name", "").strip()
                resume_email = resume_parsed.get("email", "").strip()
                resume_phone = resume_parsed.get("phone", "").strip()
                
                is_duplicate = False
                match_reasons = []
                
                # Check name match
                if name and resume_name:
                    if self.normalize_text(name) == self.normalize_text(resume_name):
                        is_duplicate = True
                        match_reasons.append("name")
                
                # Check email match
                if email and resume_email:
                    if self.normalize_email(email) == self.normalize_email(resume_email):
                        is_duplicate = True
                        match_reasons.append("email")
                
                # Check phone match
                if phone and resume_phone:
                    if self.normalize_phone(phone) == self.normalize_phone(resume_phone):
                        is_duplicate = True
                        match_reasons.append("phone")
                
                if is_duplicate:
                    duplicates.append({
                        "resume_id": str(resume["_id"]),
                        "filename": resume.get("filename", ""),
                        "candidate_name": resume_name,
                        "candidate_email": resume_email,
                        "candidate_phone": resume_phone,
                        "uploaded_at": resume.get("created_at"),
                        "uploaded_by": resume.get("uploaded_by"),
                        "match_reasons": match_reasons,
                        "status": resume.get("status", "submission")
                    })
            
            return duplicates
            
        except Exception as e:
            print(f"Error checking duplicates: {str(e)}")
            return []
    
    async def check_duplicate_by_text_content(self, text_content: str) -> List[Dict[str, Any]]:
        """
        Check for duplicates by extracting basic info from text content
        This is a fallback when parsed data is not available
        """
        try:
            # Extract basic information from text
            name = self.extract_name_from_text(text_content)
            email = self.extract_email_from_text(text_content)
            phone = self.extract_phone_from_text(text_content)
            
            if not name and not email and not phone:
                return []
            
            # Use the same logic as parsed data check
            parsed_data = {
                "name": name,
                "email": email,
                "phone": phone
            }
            
            return await self.check_duplicate_by_parsed_data(parsed_data)
            
        except Exception as e:
            print(f"Error checking duplicates from text: {str(e)}")
            return []
    
    def extract_name_from_text(self, text: str) -> str:
        """Extract candidate name from resume text"""
        try:
            # Look for common name patterns
            lines = text.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if len(line) > 2 and len(line) < 50:
                    # Skip lines that look like headers or contact info
                    if not any(word in line.lower() for word in ['email', 'phone', 'address', 'resume', 'cv']):
                        # Check if it looks like a name (contains letters and spaces)
                        if re.match(r'^[A-Za-z\s\.]+$', line) and len(line.split()) >= 2:
                            return line
            return ""
        except:
            return ""
    
    def extract_email_from_text(self, text: str) -> str:
        """Extract email from resume text"""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            matches = re.findall(email_pattern, text)
            return matches[0] if matches else ""
        except:
            return ""
    
    def extract_phone_from_text(self, text: str) -> str:
        """Extract phone number from resume text"""
        try:
            # Look for phone number patterns
            phone_patterns = [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
                r'\b\d{10}\b',  # 10 digits
                r'\b\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'  # International
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0]
            return ""
        except:
            return ""


async def check_resume_duplicates(db, parsed_data: Dict[str, Any], text_content: str = None) -> List[Dict[str, Any]]:
    """
    Main function to check for duplicate resumes
    """
    checker = DuplicateResumeChecker(db)
    
    # First try with parsed data
    duplicates = await checker.check_duplicate_by_parsed_data(parsed_data)
    
    # If no duplicates found and we have text content, try text-based checking
    if not duplicates and text_content:
        duplicates = await checker.check_duplicate_by_text_content(text_content)
    
    return duplicates


async def remove_duplicate_resumes(db, duplicate_ids: List[str]) -> Dict[str, Any]:
    """
    Remove duplicate resumes from database
    """
    try:
        # Convert string IDs to ObjectId
        object_ids = [ObjectId(dup_id) for dup_id in duplicate_ids]
        
        # Delete the duplicate resumes
        result = await db.resumes.delete_many({
            "_id": {"$in": object_ids}
        })
        
        return {
            "deleted_count": result.deleted_count,
            "deleted_ids": duplicate_ids,
            "success": True
        }
        
    except Exception as e:
        print(f"Error removing duplicates: {str(e)}")
        return {
            "deleted_count": 0,
            "deleted_ids": [],
            "success": False,
            "error": str(e)
        }
