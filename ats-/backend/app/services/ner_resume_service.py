#!/usr/bin/env python3
"""
Enhanced resume parsing service using Hugging Face NER model
"""

import asyncio
import hashlib
import random
import time
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch
import spacy

# Suppress verbose device messages from ML libraries
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("torch").setLevel(logging.WARNING)

# Global model cache
_sbert_model = None
_ner_model = None
_ner_pipeline = None
_spacy_model = None

# Global versioning for experience extraction (bump when logic changes)
EXPERIENCE_EXTRACTION_VERSION = "exp_v3_2025_11_05"

def _get_sbert_model():
    """Get or initialize Sentence BERT model"""
    global _sbert_model
    if _sbert_model is None:
        print("Loading SentenceTransformer model (one-time)...")
        _sbert_model = SentenceTransformer('all-mpnet-base-v2')
    return _sbert_model

def _get_ner_model():
    """Get or initialize NER model - using resume-specific Hugging Face model"""
    global _ner_model, _ner_pipeline
    if _ner_pipeline is None:
        try:
            print("Loading Resume-Specific NER model (one-time)...")
            # Use resume-specific NER model trained on 22,542 resumes
            # yashpwr/resume-ner-bert-v2: 90.87% F1 score, 25 entity types
            model_name = "yashpwr/resume-ner-bert-v2"
            
            print(f"   Loading model: {model_name}")
            print(f"   This model is specifically trained for resume parsing (90.87% F1 score)")
            print(f"   It recognizes: Name, Email, Phone, Companies, Designation, Skills, Experience, Education, etc.")
            
            # Create NER pipeline directly from model name
            _ner_pipeline = pipeline(
                "token-classification",
                model=model_name,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            print("[SUCCESS] Resume-Specific NER model loaded successfully!")
            print(f"   Model recognizes 25 entity types: Name, Email, Phone, Location, Companies, Designation, Skills, etc.")
            return _ner_pipeline
        except Exception as e:
            print(f"[WARNING] Resume-Specific NER model loading failed: {e}")
            print(f"   Trying fallback model (dslim/bert-base-NER)...")
            try:
                # Fallback to generic NER model
                model_name = "dslim/bert-base-NER"
                print(f"   Loading fallback model: {model_name}")
                _ner_pipeline = pipeline(
                    "ner",
                    model=model_name,
                    aggregation_strategy="simple",
                    device=0 if torch.cuda.is_available() else -1
                )
                print("[SUCCESS] Fallback NER model loaded successfully!")
                return _ner_pipeline
            except Exception as e2:
                print(f"[ERROR] Fallback NER model also failed: {e2}")
            _ner_pipeline = None
    return _ner_pipeline

def _get_spacy_model():
    """Get or initialize spaCy model"""
    global _spacy_model
    if _spacy_model is None:
        try:
            print("Loading spaCy model (one-time)...")
            import sys
            import os
            
            # Try method 1: Import and load via package
            try:
                import en_core_web_sm
                print(f"   Model package found at: {en_core_web_sm.__path__}")
                _spacy_model = en_core_web_sm.load()
                print("[SUCCESS] spaCy model loaded successfully via package import!")
                return _spacy_model
            except (ImportError, OSError) as e:
                print(f"   Method 1 failed: {type(e).__name__}: {e}")
            
            # Try method 2: Use spacy.load() with model name
            try:
                _spacy_model = spacy.load("en_core_web_sm")
                print("[SUCCESS] spaCy model loaded successfully via spacy.load()!")
                return _spacy_model
            except OSError as e:
                print(f"   Method 2 failed: {e}")
            
            # Try method 3: Use direct path from package
            try:
                import en_core_web_sm
                model_path = en_core_web_sm.__path__[0]
                print(f"   Trying direct path: {model_path}")
                _spacy_model = spacy.load(model_path)
                print("[SUCCESS] spaCy model loaded successfully via direct path!")
                return _spacy_model
            except Exception as e:
                print(f"   Method 3 failed: {type(e).__name__}: {e}")
            
            # All methods failed
            print("[ERROR] All spaCy model loading methods failed")
            return None
        except Exception as e:
            print(f"[ERROR] spaCy model loading failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            import sys
            print(f"   Python executable: {sys.executable}")
            print(f"   Python version: {sys.version}")
            print(f"   Working directory: {os.getcwd()}")
            print(f"   Python path entries:")
            for p in sys.path[:5]:  # Show first 5 entries
                print(f"     - {p}")
            _spacy_model = None
    return _spacy_model

def extract_entities_with_ner(resume_text: str, skip_experience: bool = False, skip_education: bool = False, parsed_resume_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract entities using hybrid NER + spaCy approach
    
    Args:
        resume_text: Raw resume text
        skip_experience: If True, skip experience extraction (use when cache available)
        skip_education: If True, skip education extraction (not used in scoring)
        parsed_resume_data: Optional cached parsed resume data from upload time
    """
    try:
        # Removed excessive debug prints for performance
        
        # OPTIMIZATION: Use cached data completely if available - skip all extraction
        if parsed_resume_data:
            cached_name = parsed_resume_data.get("candidate_name")
            cached_email = parsed_resume_data.get("email")
            cached_phone = parsed_resume_data.get("phone")
            cached_location = parsed_resume_data.get("location")
            cached_skills = parsed_resume_data.get("skills", [])
            
            # If we have complete cached data, use it directly - NO EXTRACTION NEEDED
            if cached_name and cached_name != "Unknown" and cached_skills:
                # Use cached data completely - skip all NER/preprocessing
                ner_result = {
                    "candidate_name": cached_name,
                    "email": cached_email or "",
                    "phone": cached_phone or "",
                    "location": cached_location or "",
                    "skills": cached_skills or [],
                    "companies": [],
                    "job_titles": []
                }
            else:
                # Partial cache - only extract missing parts
                from app.services.parse_store import _preprocess_text_for_extraction
                resume_text_processed = _preprocess_text_for_extraction(resume_text)
                ner_result = _extract_basic_entities_with_ner(resume_text_processed)
                # Use cached data where available
                if cached_email:
                    ner_result["email"] = cached_email
                if cached_phone:
                    ner_result["phone"] = cached_phone
                if cached_location:
                    ner_result["location"] = cached_location
                if cached_skills:
                    ner_result["skills"] = cached_skills
        else:
            # No cached data - do full extraction
            from app.services.parse_store import _preprocess_text_for_extraction
            resume_text_processed = _preprocess_text_for_extraction(resume_text)
            ner_result = _extract_basic_entities_with_ner(resume_text_processed)
            
            # Only use fallback if extraction completely failed
            if (ner_result.get("candidate_name", "").strip() in ["Unknown", "h Patel", ""] or 
                len(ner_result.get("candidate_name", "")) < 3 or
                len(ner_result.get("skills", [])) == 0):
                fallback_result = _fallback_extraction(resume_text_processed)
                ner_result.update({
                    "candidate_name": fallback_result.get("candidate_name", "Unknown"),
                    "email": fallback_result.get("email", ""),
                    "phone": fallback_result.get("phone", ""),
                    "location": fallback_result.get("location", ""),
                    "skills": fallback_result.get("skills", [])
                })
        
        # Determine which text to use for experience/education extraction (if needed)
        # Only preprocess if we actually need to extract experience/education
        if skip_experience and skip_education:
            text_for_extraction = resume_text  # Not needed, use raw text
        else:
            if 'resume_text_processed' not in locals():
                from app.services.parse_store import _preprocess_text_for_extraction
                resume_text_processed = _preprocess_text_for_extraction(resume_text)
            text_for_extraction = resume_text_processed
        
        # OPTIMIZATION: Skip experience extraction if cache available (saves 2-5 seconds per resume)
        if skip_experience:
            print(f"[EXTRACT ENTITIES] ⚡ Skipping experience extraction (using cache)")
            spacy_experience = []
        else:
            print(f"[EXTRACT ENTITIES] Calling extract_experience_with_spacy...")
            spacy_experience = extract_experience_with_spacy(text_for_extraction)
            print(f"[EXTRACT ENTITIES] extract_experience_with_spacy returned {len(spacy_experience)} entries")
        
        # OPTIMIZATION: Skip education extraction (not used in scoring - saves time)
        if skip_education:
            print(f"[EXTRACT ENTITIES] ⚡ Skipping education extraction (not used in scoring)")
            spacy_education = []
        else:
            spacy_education = extract_education_with_spacy(text_for_extraction)
        
        # Combine results
        result = {
            "candidate_name": ner_result.get("candidate_name", "Unknown"),
            "email": ner_result.get("email", ""),
            "phone": ner_result.get("phone", ""),
            "location": ner_result.get("location", ""),
            "skills": ner_result.get("skills", []),
            "companies": ner_result.get("companies", []),
            "job_titles": ner_result.get("job_titles", []),
            "education": spacy_education,
            "experience": spacy_experience,
            "experience_level": _determine_experience_level(ner_result.get("job_titles", []), text_for_extraction)
        }
        
        # Safely print extraction results (handle Unicode characters)
        try:
            safe_name = result['candidate_name'].encode('ascii', errors='replace').decode('ascii') if result.get('candidate_name') else 'Unknown'
            print(f"Hybrid extraction completed: {safe_name} - {len(result['skills'])} skills, {len(result['experience'])} experiences, {len(result['education'])} education")
        except Exception:
            print(f"Hybrid extraction completed: [name contains non-ASCII] - {len(result['skills'])} skills, {len(result['experience'])} experiences, {len(result['education'])} education")
        return result
        
    except Exception as e:
        print(f"Hybrid extraction error: {e}")
        return _fallback_extraction(resume_text)

def _extract_basic_entities_with_ner(resume_text: str) -> Dict[str, Any]:
    """Extract basic entities using NER model or fallback"""
    try:
        # Try NER model first
        ner_pipeline = _get_ner_model()
        if ner_pipeline is not None:
            print("Using NER model for basic entities...")
            entities = ner_pipeline(resume_text)
            
            # Organize entities by type
            organized_entities = {
                "names": [],
                "emails": [],
                "phones": [],
                "skills": [],
                "companies": [],
                "jobs": [],
                "education": []
            }
            
            print(f"[NER] Found {len(entities)} entities from Resume-Specific NER model")
            
            # Map resume-specific entity types to our categories
            # yashpwr/resume-ner-bert-v2 uses: Name, Email Address, Phone, Location, Companies worked at, 
            # Designation, Skills, Years of Experience, Degree, College Name, Graduation Year, etc.
            
            for entity in entities:
                entity_group = entity.get('entity_group', '').strip()
                word = entity.get('word', '').strip()
                score = entity.get('score', 0.0)
                
                # Clean up tokenization artifacts more aggressively
                word = word.replace('##', '').replace('▁', ' ').replace('Ġ', ' ').strip()
                word = ' '.join(word.split())  # Remove extra spaces
                
                # Skip empty or invalid words
                if not word or len(word) < 2 or word.startswith('[') or word.startswith('##'):
                    continue
                    
                print(f"[NER] Entity: {entity_group} = '{word}' (score: {score:.2f})")
                    
                # Resume-specific model uses lower thresholds (better trained)
                min_score = 0.3  # Lower threshold for resume-specific model
                if score > min_score:
                    # Map resume-specific entity types to our categories
                    entity_group_upper = entity_group.upper()
                    
                    # Name extraction - check both exact match and case-insensitive
                    # The resume-ner-bert-v2 model uses "Name" (not "NAME" or "PERSON")
                    if (entity_group_upper in ['NAME', 'NAME:', 'PERSON'] or 
                        entity_group.lower() in ['name', 'person'] or
                        'name' in entity_group.lower()):
                        # Filter out common false positives for names
                        invalid_names = ['email', 'phone', 'address', 'location', 'web', 'ind', 'ql', 'hindi', 'english', 
                                       'resume', 'cv', 'contact', 'skills', 'languages', 'hobbies', 'profile', 'summary',
                                       'education', 'experience', 'bachelor', 'master', 'degree', 'university', 'college',
                                       'unknown', 'languages7026720645', 'adityaddd', 'ad', 'ityaddd']
                        if word.lower() not in invalid_names and len(word) >= 3:
                            organized_entities["names"].append(word)
                            print(f"[NER] [OK] Added NAME: '{word}' (entity_group: '{entity_group}')")
                    
                    # Email extraction - check both exact match and case-insensitive
                    # The resume-ner-bert-v2 model uses "Email Address" (not just "EMAIL")
                    elif (entity_group_upper in ['EMAIL', 'EMAIL ADDRESS', 'EMAIL:', 'E-MAIL'] or
                          'email' in entity_group.lower()):
                        # Clean up email (remove spaces added by tokenization)
                        email_clean = word.replace(' ', '').replace(' . ', '.').replace(' @ ', '@')
                        if '@' in email_clean and '.' in email_clean:
                            organized_entities["emails"].append(email_clean)
                            print(f"[NER] [OK] Added EMAIL: '{email_clean}' (entity_group: '{entity_group}')")
                    
                    # Phone extraction - check both exact match and case-insensitive
                    # The resume-ner-bert-v2 model uses "Phone" (not "PHONE NUMBER")
                    elif (entity_group_upper in ['PHONE', 'PHONE NUMBER', 'PHONE:', 'MOBILE', 'TELEPHONE'] or
                          'phone' in entity_group.lower()):
                        # Clean up phone (remove spaces added by tokenization)
                        phone_clean = word.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                        if any(char.isdigit() for char in phone_clean) and len(phone_clean) >= 7:
                            organized_entities["phones"].append(word)  # Keep original format for display
                            print(f"[NER] [OK] Added PHONE: '{word}' (entity_group: '{entity_group}')")
                    
                    # Companies extraction - check both exact match and case-insensitive
                    # The resume-ner-bert-v2 model uses "Companies worked at" (not just "COMPANY")
                    elif (entity_group_upper in ['COMPANIES WORKED AT', 'COMPANY', 'ORGANIZATION', 'ORG', 'EMPLOYER'] or
                          'compan' in entity_group.lower() or 'organization' in entity_group.lower()):
                        organized_entities["companies"].append(word)
                        print(f"[NER] [OK] Added COMPANY: '{word}' (entity_group: '{entity_group}')")
                    
                    # Job titles extraction - check both exact match and case-insensitive
                    # The resume-ner-bert-v2 model uses "Designation" (not "JOB TITLE")
                    elif (entity_group_upper in ['DESIGNATION', 'JOB TITLE', 'POSITION', 'ROLE', 'JOB'] or
                          'designation' in entity_group.lower() or 'position' in entity_group.lower() or
                          'role' in entity_group.lower()):
                        organized_entities["jobs"].append(word)
                        print(f"[NER] [OK] Added JOB TITLE: '{word}' (entity_group: '{entity_group}')")
                    
                    # Skills extraction
                    elif entity_group_upper in ['SKILLS', 'SKILL', 'TECHNICAL SKILLS', 'SOFT SKILLS']:
                        if word.lower() not in ['script', 'act', 'java', 'script']:
                            organized_entities["skills"].append(word)
                            print(f"[NER] [OK] Added SKILL: '{word}'")
                    
                    # Education extraction
                    elif entity_group_upper in ['DEGREE', 'EDUCATION', 'COLLEGE NAME', 'GRADUATION YEAR', 'UNIVERSITY']:
                        organized_entities["education"].append(word)
                        print(f"[NER] [OK] Added EDUCATION: '{word}'")
                    
                    # Experience extraction
                    elif entity_group_upper in ['YEARS OF EXPERIENCE', 'EXPERIENCE', 'WORK EXPERIENCE']:
                        # Store experience years separately if needed
                        organized_entities["education"].append(word)  # Placeholder
                        print(f"[NER] [OK] Added EXPERIENCE: '{word}'")
                    
                    # Location extraction
                    elif entity_group_upper in ['LOCATION', 'LOC', 'ADDRESS', 'CITY', 'STATE']:
                        # Location can be stored separately if needed
                        print(f"[NER] [OK] Found LOCATION: '{word}'")
            
            # Process and clean entities
            result = {
                "candidate_name": _extract_best_name(organized_entities["names"]),
                "email": _extract_best_email(organized_entities["emails"]),
                "phone": _extract_best_phone(organized_entities["phones"]),
                "location": _extract_location_from_text(resume_text),
                "skills": list(set(organized_entities["skills"])),
                "companies": list(set(organized_entities["companies"])),
                "job_titles": list(set(organized_entities["jobs"])),
            }
            
            # Safely print NER extracted info (handle Unicode characters)
            try:
                safe_name = result['candidate_name'].encode('ascii', errors='replace').decode('ascii') if result.get('candidate_name') else 'Unknown'
                print(f"NER extracted: {safe_name}, {len(result['skills'])} skills")
            except Exception:
                print(f"NER extracted: [name contains non-ASCII], {len(result['skills'])} skills")
            return result
        else:
            print("NER model not available, using fallback...")
            return _fallback_extraction(resume_text)
            
    except Exception as e:
        print(f"NER extraction error: {e}")
        return _fallback_extraction(resume_text)

def _fallback_extraction(resume_text: str) -> Dict[str, Any]:
    """Fallback extraction using regex patterns"""
    try:
        # Import name extraction from parse_store for consistency
        from app.services.parse_store import extract_name_from_text, _preprocess_text_for_extraction
        
        # Preprocess text first (handles concatenated text from PDF)
        resume_text = _preprocess_text_for_extraction(resume_text)
        
        # Use the improved name extraction
        candidate_name = extract_name_from_text(resume_text)
        
        if not candidate_name or candidate_name == "":
            candidate_name = "Unknown"
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, resume_text)
        email = email_match.group() if email_match else ""
        
        # Extract phone
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',  # (123) 456-7890
            r'\b\d{10}\b',  # 1234567890
            r'\b\d{5}[-.]?\d{5}\b',  # 12345-67890 (Indian format)
            r'\b\d{3}\s*\d{3}\s*\d{4}\b',  # 123 456 7890
            r'\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}\b',  # +1 123 456 7890
        ]
        
        phone = ""
        for pattern in phone_patterns:
            phone_match = re.search(pattern, resume_text)
            if phone_match:
                phone = phone_match.group()
                break
        
        # Extract skills using comprehensive keyword matching
        tech_skills = [
            # Programming Languages
            "python", "javascript", "java", "typescript", "php", "ruby", "go", "rust", 
            "c++", "c#", "swift", "kotlin", "scala", "r", "matlab", "perl", "lua",
            # Web Technologies
            "html", "css", "react", "angular", "vue", "node.js", "express", "django", 
            "flask", "spring", "laravel", "rails", "asp.net", "jquery", "bootstrap", 
            "tailwind", "sass", "less", "webpack", "babel", "npm", "yarn",
            # Databases
            "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle", "sql server",
            "cassandra", "elasticsearch", "dynamodb", "firebase", "supabase",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "gitlab", "github",
            "terraform", "ansible", "nginx", "apache", "linux", "ubuntu", "centos",
            # Mobile & Frameworks
            "react native", "flutter", "xamarin", "ionic", "cordova", "expo",
            # Data Science & AI
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
            "seaborn", "jupyter", "spark", "hadoop", "kafka", "airflow",
            # Tools & Others
            "git", "github", "gitlab", "bitbucket", "jira", "confluence", "slack",
            "figma", "sketch", "adobe", "photoshop", "illustrator", "wordpress",
            "drupal", "magento", "shopify", "salesforce", "tableau", "power bi"
        ]
        
        found_skills = []
        resume_lower = resume_text.lower()
        for skill in tech_skills:
            if skill in resume_lower:
                found_skills.append(skill.title())
        
        # Also extract skills from explicit skill sections
        skill_section_patterns = [
            r'Skills?[:\s]*([^.\n]+)',
            r'Technical Skills?[:\s]*([^.\n]+)',
            r'Technologies?[:\s]*([^.\n]+)',
            r'Programming Languages?[:\s]*([^.\n]+)',
            r'Tools?[:\s]*([^.\n]+)',
            r'Frameworks?[:\s]*([^.\n]+)',
        ]
        
        for pattern in skill_section_patterns:
            matches = re.finditer(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                skill_text = match.group(1).strip()
                # Split by common separators
                skill_list = re.split(r'[,;|•\n]', skill_text)
                for skill in skill_list:
                    skill = skill.strip()
                    if len(skill) > 1 and len(skill) < 50:
                        found_skills.append(skill.title())
        
        unique_skills = []
        seen = set()
        for s in found_skills:
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique_skills.append(s)
        return {
            "candidate_name": candidate_name,
            "email": email,
            "phone": phone,
            "skills": unique_skills,
            "companies": [],
            "job_titles": [],
            "education": [],
            "location": _extract_location_from_text(resume_text),
            "experience_level": _determine_experience_level([], resume_text)
        }
        
    except Exception as e:
        print(f"Fallback extraction error: {e}")
        return {
            "candidate_name": "Unknown",
            "email": "",
            "phone": "",
            "skills": [],
            "companies": [],
            "job_titles": [],
            "education": [],
            "location": "",
            "experience_level": "Unknown"
        }

def _extract_best_name(names: List[str]) -> str:
    """Extract the best candidate name from NER results"""
    if not names:
        return "Unknown"
    
    # Filter out invalid names
    valid_names = [name for name in names if len(name) > 2 and not name.startswith('##')]
    
    if not valid_names:
        return "Unknown"
    
    # Prefer full names (3+ words) over single words
    # Full names are more reliable (e.g., "ADITYA KUMAR PANDEY" vs "Adityaddd")
    full_names = [name for name in valid_names if len(name.split()) >= 2]
    if full_names:
        # Return the longest full name (most complete)
        best_name = max(full_names, key=lambda n: (len(n.split()), len(n)))
        print(f"[NER] Selected best name (full name): '{best_name}' from {valid_names}")
        return best_name
    
    # Fallback: Return the longest single-word name
    best_name = max(valid_names, key=len)
    print(f"[NER] Selected best name (single word): '{best_name}' from {valid_names}")
    return best_name

def _extract_best_email(emails: List[str]) -> str:
    """Extract the best email from NER results"""
    if not emails:
        return ""
    
    # Return the first valid email
    for email in emails:
        if '@' in email and '.' in email:
            return email
    return emails[0] if emails else ""

def _extract_best_phone(phones: List[str]) -> str:
    """Extract the best phone number from NER results"""
    if not phones:
        return ""
    
    # Return the longest phone number (most complete)
    return max(phones, key=len)

def _extract_location_from_text(resume_text: str) -> str:
    """Extract location using regex patterns"""
    try:
        location_patterns = [
            r'(?:Location|Address|Based in|Located in):\s*([^,\n]+)',
            r'([A-Z][a-z]+,\s*[A-Z]{2})',
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)'
        ]
        
        for pattern in location_patterns:
            location_match = re.search(pattern, resume_text, re.IGNORECASE)
            if location_match:
                return location_match.group(1).strip()
        return ""
    except:
        return ""

def _clean_experience_context(context: str) -> str:
    """Clean experience context to remove personal contact information"""
    try:
        # Remove common personal contact patterns
        personal_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b(?:www\.|https?://)[^\s]+\b',  # Websites/URLs
            r'\b(?:phone|email|contact|mobile|tel)[:\s]*[^\n]+',  # Contact labels
            r'\b(?:linkedin|github|portfolio|website)[:\s]*[^\n]+',  # Social media
        ]
        
        cleaned_context = context
        for pattern in personal_patterns:
            cleaned_context = re.sub(pattern, '', cleaned_context, flags=re.IGNORECASE)
        
        # Remove extra whitespace and clean up
        cleaned_context = re.sub(r'\s+', ' ', cleaned_context).strip()
        
        return cleaned_context
    except:
        return context

def _normalize_year_in_date(date_str: str) -> str:
    """Normalize 2-digit years to 4-digit years (e.g., 'July 25' -> 'July 2025', 'Feb 24' -> 'Feb 2024')"""
    if not date_str:
        return date_str
    
    # Check if date contains a 2-digit year (20-99 interpreted as 2020-2099)
    # Pattern: month name followed by 2-digit number (20-99)
    date_str_clean = date_str.strip()
    
    # Match patterns like "July 25", "Feb 24", "January 20"
    # Look for month name followed by 2-digit number (20-99)
    two_digit_year_pattern = r'(\w+)\s+(\d{2})\b'
    match = re.search(two_digit_year_pattern, date_str_clean, re.IGNORECASE)
    
    if match:
        month_part = match.group(1)
        year_part = match.group(2)
        year_int = int(year_part)
        
        # If it's 20-99, interpret as 2020-2099
        if 20 <= year_int <= 99:
            normalized_year = f"20{year_int}"
            normalized_date = date_str_clean.replace(f"{month_part} {year_part}", f"{month_part} {normalized_year}")
            return normalized_date
    
    # Also handle standalone 2-digit years (e.g., "24", "25")
    if date_str_clean.isdigit() and len(date_str_clean) == 2:
        year_int = int(date_str_clean)
        if 20 <= year_int <= 99:
            return f"20{year_int}"
    
    return date_str

def _is_valid_date_range(start_date: str, end_date: str) -> bool:
    """Validate that the date range is reasonable and not a phone number"""
    try:
        # Extract year from start_date (handles MM/YYYY, YYYY/MM, Month Year, Year-only formats)
        start_year = None
        if start_date:
            # Try MM/YYYY or YYYY/MM format
            if '/' in start_date or '-' in start_date:
                parts = re.split(r'[/-]', start_date)
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        start_year = int(part)
                        break
            # Try year-only format
            elif start_date.isdigit() and len(start_date) == 4:
                start_year = int(start_date)
            # Try month-year format
            elif ' ' in start_date:
                parts = start_date.split()
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        start_year = int(part)
                        break
            # Extract year from any 4-digit number
            else:
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', start_date)
                if year_match:
                    start_year = int(year_match.group(1))
        
        if start_year and not (1950 <= start_year <= 2030):
                    return False
        
        # Extract year from end_date (handles various formats)
        if end_date not in ['present', 'current', 'now']:
            end_year = None
            if end_date:
                # Try MM/YYYY or YYYY/MM format
                if '/' in end_date or '-' in end_date:
                    parts = re.split(r'[/-]', end_date)
                    for part in parts:
                        if part.isdigit() and len(part) == 4:
                            end_year = int(part)
                            break
                # Try year-only format
                elif end_date.isdigit() and len(end_date) == 4:
                    end_year = int(end_date)
                # Try month-year format
                elif ' ' in end_date:
                    parts = end_date.split()
                    for part in parts:
                        if part.isdigit() and len(part) == 4:
                            end_year = int(part)
                            break
                    # If no 4-digit year found in split, try regex
                    if end_year is None:
                        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', end_date)
                        if year_match:
                            end_year = int(year_match.group(1))
                # Extract year from any 4-digit number (fallback)
                else:
                    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', end_date)
                    if year_match:
                        end_year = int(year_match.group(1))
                
                if end_year and not (1950 <= end_year <= 2030):
                    return False
                
                # Validate that end_year >= start_year (if both are known)
                if start_year and end_year and end_year < start_year:
                        return False
        
        # Additional check: ensure it's not a phone number pattern
        # Only apply this check if both dates are pure numbers (not month-year formats)
        start_is_pure_number = start_date.replace('/', '').replace('-', '').replace(' ', '').isdigit()
        end_is_pure_number = end_date.replace('/', '').replace('-', '').replace(' ', '').isdigit() if end_date not in ['present', 'current', 'now'] else False
        
        if start_date and end_date and start_is_pure_number and end_is_pure_number:
            # Check if it looks like a phone number (too many digits in sequence)
            combined = start_date.replace('/', '').replace('-', '').replace(' ', '') + end_date.replace('/', '').replace('-', '').replace(' ', '')
            if len(combined) > 8:  # Years are 4 digits each = 8 total, phone numbers are 10+
                return False
        
        # If we have at least one valid year, consider it valid
        if start_year or (end_date in ['present', 'current', 'now']):
            return True
        
        return False
    except:
        return False

def _looks_like_work_experience(context: str) -> bool:
    """Check if the context looks like work experience"""
    try:
        context_lower = context.lower()
        
        # Must NOT contain education keywords (strong filter)
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma', 'certificate',
            'university', 'college', 'institute', 'school', 'graduated', 'graduation',
            'b.tech', 'm.tech', 'b.s', 'm.s', 'mba', 'bachelor of', 'master of',
            'student', 'studied', 'course', 'curriculum', 'gpa', 'cgpa', 'grade',
            'expected 2026', 'expected 2025', 'expected 2024',  # Education years
            'coursework', 'academic', 'thesis', 'dissertation'
        ]
        
        # If it has strong education indicators, it's NOT work experience
        if any(edu_word in context_lower for edu_word in education_keywords):
            return False
        
        # Check for skills section indicators (common false positives)
        skills_keywords = [
            'skills', 'languages', 'frameworks', 'tools', 'technologies',
            'proficient in', 'familiar with', 'expertise in',
            'programming languages', 'software tools'
        ]
        
        # If context is mostly skills keywords, it's likely not experience
        skills_count = sum(1 for keyword in skills_keywords if keyword in context_lower)
        if skills_count >= 2:  # Multiple skills keywords
            return False
        
        # Must NOT contain project keywords (projects are not work experience)
        project_keywords = [
            'project', 'github', 'repository', 'repo', 'personal project', 'academic project',
            'side project', 'hackathon', 'competition', 'contest'
        ]
        
        if any(proj_word in context_lower for proj_word in project_keywords):
            # Allow if it also has work keywords (project at work)
            work_keywords_present = any(keyword in context_lower for keyword in ['engineer', 'developer', 'work', 'job', 'position', 'at ', 'company'])
            if not work_keywords_present:
                return False
        
        # Must contain work-related keywords
        work_keywords = [
            'engineer', 'developer', 'designer', 'manager', 'analyst', 'specialist',
            'consultant', 'freelancer', 'contractor', 'intern', 'assistant',
            'director', 'lead', 'senior', 'junior', 'coordinator', 'supervisor',
            'programmer', 'architect', 'consultant', 'advisor', 'executive',
            'web', 'software', 'technical', 'professional', 'work', 'job', 'position',
            'employment', 'employed', 'worked', 'experience', 'career'
        ]
        
        # Must contain company indicators
        company_indicators = [
            'at ', 'company', 'corp', 'inc', 'llc', 'ltd', 'solutions', 'technologies',
            'systems', 'services', 'group', 'associates', 'partners', 'innovation',
            'freelancer', 'contract', 'client'
        ]
        
        # Must NOT contain personal information
        personal_indicators = [
            'phone', 'email', 'contact', 'address', 'location', 'www', 'http',
            'gmail', 'yahoo', 'hotmail', 'linkedin', 'github'
        ]
        
        # Check for work keywords
        has_work_keywords = any(keyword in context_lower for keyword in work_keywords)
        
        # Check for company indicators
        has_company_indicators = any(indicator in context_lower for indicator in company_indicators)
        
        # Check for personal information (should NOT be present)
        has_personal_info = any(indicator in context_lower for indicator in personal_indicators)
        
        # More strict: must have work keywords AND company indicators, and no personal info
        return has_work_keywords and has_company_indicators and not has_personal_info
        
    except:
        return False  # If we can't determine, be conservative and reject

def _calculate_years_for_single_entry(start_date: str, end_date: str) -> float:
    """Calculate years of experience for a single date range"""
    try:
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
            'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
            'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
            'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
            'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        # Parse start date
        start_year = None
        start_month = 1
        start_date_clean = str(start_date).strip()
        
        if ' ' in start_date_clean:
            parts = start_date_clean.split()
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    start_year = int(part)
                    break
            for part in parts:
                part_lower = part.lower()
                if part_lower in month_map:
                    start_month = month_map[part_lower]
                    break
        elif start_date_clean.isdigit() and len(start_date_clean) == 4:
            start_year = int(start_date_clean)
        
        if not start_year or not (1950 <= start_year <= 2030):
            return 0.0
        
        # Parse end date
        end_year = None
        end_month = 1
        end_date_clean = str(end_date).strip().lower()
        
        if end_date_clean in ['present', 'current', 'now']:
            end_year = current_year
            end_month = current_month
        elif ' ' in end_date_clean:
            parts = end_date_clean.split()
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    end_year = int(part)
                    break
            for part in parts:
                part_lower = part.lower()
                if part_lower in month_map:
                    end_month = month_map[part_lower]
                    break
        elif end_date_clean.isdigit() and len(end_date_clean) == 4:
            end_year = int(end_date_clean)
        
        if not end_year or not (1950 <= end_year <= 2030):
            return 0.0
        
        if end_year < start_year:
            return 0.0
        
        # Calculate years
        if end_year == start_year:
            months_diff = end_month - start_month + 1
            if months_diff < 0:
                months_diff = 12 + months_diff
            return months_diff / 12.0
        else:
            years = end_year - start_year
            months = end_month - start_month
            if months < 0:
                years -= 1
                months += 12
            total_months = years * 12 + months + 1
            return total_months / 12.0
    except Exception as e:
        print(f"[EXPERIENCE EXTRACT] Error calculating years for {start_date} - {end_date}: {e}")
        return 0.0

def extract_experience_with_spacy(resume_text: str) -> List[Dict[str, Any]]:
    """Extract experience entries using regex + context rules + spaCy support"""
    # Normalize common unicode artifacts before any processing (generic)
    resume_text = resume_text.replace('\u00A0', ' ').replace('\u200b', '').replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')
    resume_text = re.sub(r'\(cid:\d+\)', ' ', resume_text)
    resume_text = resume_text.replace('\u2013', '-').replace('\u2014', '-')
    # Also ensure letters and digits are separated (helps MonthYYYY -> Month YYYY)
    resume_text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', resume_text)
    resume_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', resume_text)

    try:
        print(f"[EXPERIENCE EXTRACT] Starting extraction for resume (length: {len(resume_text)} chars)")
        nlp = _get_spacy_model()
        if nlp is None:
            print(f"[EXPERIENCE EXTRACT] ERROR: spaCy model not available, returning empty list")
            return []
        
        print(f"[EXPERIENCE EXTRACT] spaCy model loaded successfully")
        doc = nlp(resume_text)
        experiences = []
        
        # FIRST: Try to find experience sections by looking for common headers
        # Simplified: single, case-insensitive pattern for experience-style headers
        experience_section_headers = [
            r'(?i)(work\s+experience|experience|professional\s+experience)',
        ]
        
        # MULTI-SECTION EXTRACTION: Find ALL experience sections, not just the first
        experience_sections = []  # List of (start_pos, end_pos, header_name) tuples
        
        # First, find all regex matches for experience headers
        for header_idx, header_pattern in enumerate(experience_section_headers):
            for header_match in re.finditer(header_pattern, resume_text, re.IGNORECASE | re.MULTILINE):
                section_start = header_match.end()
                matched_header = header_match.group(0).strip()
                # Safely print header (handle Unicode characters)
                try:
                    safe_header = matched_header.encode('ascii', errors='replace').decode('ascii')
                    print(f"[EXPERIENCE EXTRACT] Found experience section header (pattern {header_idx}): '{safe_header}' at position {section_start}")
                except Exception:
                    print(f"[EXPERIENCE EXTRACT] Found experience section header (pattern {header_idx}) at position {section_start}")
                
                # Find the end of this experience section
                # Check for: next experience section, Education, Skills, Projects, etc.
                section_end = None
                
                # First, check if there's another experience section after this one
                # Search from a bit after section_start to avoid matching the same header
                next_exp_section_pos = len(resume_text)  # Default to end of resume
                search_from = section_start + 10  # Skip a bit to avoid matching same header
                for next_header_pattern in experience_section_headers:
                    next_match = re.search(next_header_pattern, resume_text[search_from:], re.IGNORECASE | re.MULTILINE)
                    if next_match:
                        next_pos = search_from + next_match.start()
                        if next_pos < next_exp_section_pos:
                            next_exp_section_pos = next_pos
                
                # Then check for non-experience sections (Education, Skills, etc.)
                next_section_patterns = [
                    r'\n\s*(?:education|academic|qualification|certification|skills|projects|achievements|awards|references)\s*[:]?\s*\n',
                ]
                next_non_exp_section_pos = len(resume_text)
                for next_pattern in next_section_patterns:
                    next_match = re.search(next_pattern, resume_text[section_start:], re.IGNORECASE | re.MULTILINE)
                    if next_match:
                        next_pos = section_start + next_match.start()
                        if next_pos < next_non_exp_section_pos:
                            next_non_exp_section_pos = next_pos
                
                # Section ends at whichever comes first: next experience section or non-experience section
                section_end = min(next_exp_section_pos, next_non_exp_section_pos)
                
                if section_end == len(resume_text):
                    # Safely print header (handle Unicode characters)
                    try:
                        safe_header = matched_header.encode('ascii', errors='replace').decode('ascii')
                        print(f"[EXPERIENCE EXTRACT] Experience section '{safe_header}' extends to end of resume")
                    except Exception:
                        print(f"[EXPERIENCE EXTRACT] Experience section extends to end of resume")
                else:
                    # Safely print header (handle Unicode characters)
                    try:
                        safe_header = matched_header.encode('ascii', errors='replace').decode('ascii')
                        print(f"[EXPERIENCE EXTRACT] Experience section '{safe_header}' ends at position {section_end}")
                    except Exception:
                        print(f"[EXPERIENCE EXTRACT] Experience section ends at position {section_end}")
                
                experience_sections.append((section_start, section_end, matched_header))
        
        # Remove duplicate sections (same start position)
        seen_starts = {}
        unique_sections = []
        for start, end, header in experience_sections:
            if start not in seen_starts:
                seen_starts[start] = True
                unique_sections.append((start, end, header))
            else:
                print(f"[EXPERIENCE EXTRACT] Skipping duplicate section at position {start}")
        
        experience_sections = unique_sections
        experience_sections.sort(key=lambda x: x[0])  # Sort by start position
        
        print(f"[EXPERIENCE EXTRACT] Found {len(experience_sections)} unique experience section(s)")
        
        # If no regex matches found, try semantic similarity matching
        if not experience_sections:
            # No regex match found - try semantic similarity matching as fallback
            print(f"[EXPERIENCE EXTRACT] No regex match found. Trying semantic similarity matching...")
            
            # Extract candidate header lines (first 60 lines where headers usually appear)
            lines = resume_text.split('\n')
            candidate_lines = []
            for i, line in enumerate(lines[:60]):  # Check first 60 lines
                line_clean = line.strip()
                # Filter out educational experience explicitly
                line_lower = line_clean.lower()
                if 'educational' in line_lower or 'academic experience' in line_lower:
                    # Safely print line (handle Unicode characters)
                    try:
                        safe_line = line_clean.encode('ascii', errors='replace').decode('ascii')
                        print(f"[EXPERIENCE EXTRACT] Skipping educational experience header: '{safe_line}'")
                    except Exception:
                        print(f"[EXPERIENCE EXTRACT] Skipping educational experience header")
                    continue
                
                # Look for lines that could be section headers
                if (3 <= len(line_clean) <= 80 and 
                    not line_clean.startswith(('http', 'www', '@')) and
                    not any(char.isdigit() for char in line_clean[:3]) and  # Not dates/numbers
                    line_clean.count(' ') <= 6):  # Allow up to 6 words
                    candidate_lines.append(line_clean)
            
            # Use semantic similarity to find ALL experience headers (not just first)
            all_semantic_matches = find_all_semantic_experience_headers(candidate_lines, resume_text, threshold=0.4)
            
            if all_semantic_matches:
                experience_sections.extend(all_semantic_matches)
                print(f"[EXPERIENCE EXTRACT] Found {len(all_semantic_matches)} semantic experience section(s)")
            else:
                # Fallback: Try regex keywords (keep for compatibility)
                exp_keywords = re.findall(
                    r'\b(experience|work\s+experience|professional\s+experience|employment\s+history|career\s+history|'
                    r'work\s+history|professional\s+history|job\s+experience|employment|'
                    r'internship\s+experience|internships|internship\s+history|intern\s+experience|'
                    r'summer\s+internship|winter\s+internship|training\s+experience|industrial\s+training|'
                    r'vocational\s+training|apprenticeship\s+experience|professional\s+training)\b',
                    resume_text, re.IGNORECASE
                )
                if exp_keywords:
                    print(f"[EXPERIENCE EXTRACT] DEBUG: Found experience keywords in resume: {set(exp_keywords)}")
        
        # Sort sections by start position and merge overlapping sections
        experience_sections.sort(key=lambda x: x[0])
        merged_sections = []
        for start, end, header in experience_sections:
            if merged_sections and start < merged_sections[-1][1]:
                # Overlapping section - extend the previous one
                prev_start, prev_end, prev_header = merged_sections[-1]
                merged_sections[-1] = (prev_start, max(prev_end, end), f"{prev_header} + {header}")
                print(f"[EXPERIENCE EXTRACT] Merged overlapping sections: '{prev_header}' and '{header}'")
            else:
                merged_sections.append((start, end, header))
        
        experience_sections = merged_sections
        
        # MULTI-SECTION: Extract dates from ALL experience sections
        if experience_sections:
            # Combine all experience sections into one search text
            search_text_parts = []
            for start, end, header in experience_sections:
                section_text = resume_text[start:end]
                search_text_parts.append(section_text)
                print(f"[EXPERIENCE EXTRACT] Including section '{header}' (positions {start}-{end}, {len(section_text)} chars)")
            
            search_text = "\n".join(search_text_parts)
            print(f"[EXPERIENCE EXTRACT] Searching in {len(experience_sections)} experience section(s) (total: {len(search_text)} chars)")
        else:
            # No experience section found - search entire resume but stop before Education section
            search_text = resume_text
            education_match = re.search(r'\n\s*(?:education|academic|qualification)\s*[:]?\s*\n', resume_text, re.IGNORECASE | re.MULTILINE)
            if education_match:
                search_text = resume_text[:education_match.start()]
                print(f"[EXPERIENCE EXTRACT] No experience section header - searching text before Education section")
            else:
                print(f"[EXPERIENCE EXTRACT] No experience section header - searching entire resume")
        
        print(f"[EXPERIENCE EXTRACT] Searching in {'experience section(s)' if experience_sections else 'full text'} (length: {len(search_text)} chars)")
        
        # Simplified date range patterns (month-year and year-only with optional 'Present')
        all_patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-\s*[Pp]resent',
            r'(\d{4})\s*-\s*(\d{4})',
            r'(\d{4})\s*-\s*[Pp]resent',
        ]
        
        # Track all date matches to ensure we don't miss any
        all_date_matches = []
        pattern_match_counts = {}
        
        for pattern_idx, pattern in enumerate(all_patterns):
            matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
            pattern_match_counts[pattern_idx] = len(matches)
            
            for match in matches:
                start_date_raw = match.group(1)
                end_date_raw = match.group(2).lower() if match.group(2) else "present"
                
                # Normalize 2-digit years to 4-digit years (e.g., "25" -> "2025", "24" -> "2024")
                start_date = _normalize_year_in_date(start_date_raw)
                end_date = _normalize_year_in_date(end_date_raw) if end_date_raw not in ['present', 'current', 'now'] else end_date_raw
                
                # DEBUG: Log normalization results
                if pattern_idx >= len(experience_patterns) and (start_date != start_date_raw or end_date != end_date_raw):
                    print(f"[EXPERIENCE EXTRACT] Normalized: '{start_date_raw}' -> '{start_date}', '{end_date_raw}' -> '{end_date}'")
                
                # Additional validation to avoid phone numbers and invalid dates
                is_valid = _is_valid_date_range(start_date, end_date)
                if is_valid:
                    # Map back to original resume_text position for context extraction
                    # Since we're searching in combined sections, find position in original resume_text
                    original_pos = match.start()  # Position in search_text
                    # If we have experience sections, try to map back to original text
                    if experience_sections:
                        # Find which section this match belongs to
                        cumulative_pos = 0
                        for start, end, header in experience_sections:
                            section_len = end - start
                            if original_pos < cumulative_pos + section_len:
                                # This match is in this section
                                original_pos = start + (original_pos - cumulative_pos)
                                break
                            cumulative_pos += section_len + 1  # +1 for the "\n" separator
                    else:
                        original_pos = match.start()
                    
                    # CRITICAL: Check if we've already matched this exact date range at this position
                    # This prevents the same date range from being added multiple times
                    # BUT: Only consider it a duplicate if positions are VERY close (< 20 chars apart)
                    # Different positions with same dates might be different experiences (e.g., same role at different companies)
                    date_key = (start_date, end_date, original_pos)
                    is_duplicate_date = False
                    for existing_match in all_date_matches:
                        existing_start = existing_match['start_date']
                        existing_end = existing_match['end_date']
                        existing_pos = existing_match['original_pos']
                        # If same dates and positions are very close (< 20 chars apart), it's a duplicate
                        # Increased threshold from 50 to 20 to be less aggressive - only filter true duplicates
                        if start_date == existing_start and end_date == existing_end and abs(original_pos - existing_pos) < 20:
                            is_duplicate_date = True
                            print(f"[EXPERIENCE EXTRACT] Skipping duplicate date match at position {original_pos} (same as {existing_pos}, diff: {abs(original_pos - existing_pos)} chars)")
                            break
                    
                    if not is_duplicate_date:
                        all_date_matches.append({
                            'match': match,
                            'start_date': start_date,
                            'end_date': end_date,
                            'original_pos': original_pos
                        })
                else:
                    print(f"[EXPERIENCE EXTRACT] Pattern {pattern_idx} matched '{start_date_raw} - {end_date_raw}' (normalized: '{start_date} - {end_date}') but failed validation")
        
        print(f"[EXPERIENCE EXTRACT] Pattern matches: {pattern_match_counts}")
        print(f"[EXPERIENCE EXTRACT] Found {len(all_date_matches)} potential date ranges after validation")
        
        # DEBUG: Show sample of search text if no dates found
        if len(all_date_matches) == 0 and len(search_text) > 0:
            print(f"[EXPERIENCE EXTRACT] DEBUG: No dates found. Search text preview (first 1000 chars):")
            print(f"[EXPERIENCE EXTRACT] {search_text[:1000]}")
            # Try to find any 4-digit years in the text
            year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', search_text)
            if year_matches:
                print(f"[EXPERIENCE EXTRACT] DEBUG: Found 4-digit years in text: {set(year_matches)}")
            else:
                print(f"[EXPERIENCE EXTRACT] DEBUG: No 4-digit years found in search text")
            
            # Try to find 2-digit years (like "24", "25") that might be dates
            two_digit_year_matches = re.findall(r'\b(1[5-9]|[2-9]\d)\b', search_text)
            if two_digit_year_matches:
                print(f"[EXPERIENCE EXTRACT] DEBUG: Found 2-digit numbers that might be years: {set(two_digit_year_matches[:20])}")
            
            # Look for month names followed by numbers
            month_year_patterns_debug = [
                r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{2,4})\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{2,4})\b',
            ]
            for pattern in month_year_patterns_debug:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                if matches:
                    print(f"[EXPERIENCE EXTRACT] DEBUG: Found month-year patterns: {matches[:10]}")
            
            # Look for "present" or "current" near dates
            present_matches = re.findall(r'\b(present|current)\b', search_text, re.IGNORECASE)
            if present_matches:
                print(f"[EXPERIENCE EXTRACT] DEBUG: Found 'present/current' keywords: {len(present_matches)} times")
        
        # Process each date match
        for date_info in all_date_matches:
            match = date_info['match']
            start_date = date_info['start_date']
            end_date = date_info['end_date']
            original_pos = date_info['original_pos']
            
            # Extract text around the match for context (increased window for better extraction)
            start_pos = max(0, original_pos - 400)  # Increased to 400 for better context
            end_pos = min(len(resume_text), original_pos + match.end() - match.start() + 400)
            context = resume_text[start_pos:end_pos]
            
            # Check if this is in an education section (skip if so)
            # BUT: If we found an experience section header, prioritize that - don't filter out dates in experience section
            # Generic fix: Check if we're actually IN an experience section before filtering as education
            is_in_experience_section = False
            if experience_sections:
                # Check if this date is within any of the experience sections we found
                for exp_start, exp_end, exp_header in experience_sections:
                    if exp_start <= original_pos <= exp_end:
                        is_in_experience_section = True
                        print(f"[EXPERIENCE EXTRACT] Date is within experience section '{exp_header}' (pos {original_pos} in range {exp_start}-{exp_end})")
                        break
            
            # Only check for education section if we're NOT in an experience section
            if not is_in_experience_section:
                section_start = resume_text.rfind('\n', 0, original_pos)
                section_text = resume_text[max(0, section_start-300):original_pos].lower()  # Increased window
                
                # Check for education keywords, but also check if experience keywords appear AFTER education
                # This handles cases where Education section comes before Experience section
                # If we find "experience" keyword AFTER "education" keyword, we're likely in experience section
                education_pos = section_text.rfind('education')
                experience_pos = section_text.rfind('experience')
                
                # If experience keyword appears after education keyword, we're in experience section
                if experience_pos > education_pos and experience_pos > 0:
                    print(f"[EXPERIENCE EXTRACT] Experience keyword found after education keyword - treating as experience section")
                    is_in_experience_section = True
                
                if not is_in_experience_section and any(edu_word in section_text for edu_word in ['education', 'degree', 'bachelor', 'master', 'phd', 'university', 'college', 'institute', 'school', 'graduated', 'diploma', 'expected', 'higher secondary', 'secondary school']):
                    print(f"[EXPERIENCE EXTRACT] Skipping date in education section: {start_date} - {end_date}")
                    continue  # Skip education dates
            
            # LENIENT: Filter out future dates, BUT allow if end_date is "present" (might be typo or rounding)
            # Extract year from start_date
            start_year_match = re.search(r'\b(19\d{2}|20\d{2})\b', start_date)
            if start_year_match:
                start_year = int(start_year_match.group(1))
                from datetime import datetime
                current_year = datetime.now().year
                # Only skip if start_year is significantly in the future (> 1 year) AND end_date is not "present"
                # If end_date is "present", it's likely a current job (maybe typo in year)
                if start_year > current_year + 1 and end_date not in ['present', 'current', 'now']:
                    print(f"[EXPERIENCE EXTRACT] Skipping date with future start year: {start_date} - {end_date} (start_year: {start_year} > current+1: {current_year+1})")
                    continue
                # If start_year is just 1 year ahead and end_date is "present", allow it (might be typo or upcoming start)
                elif start_year > current_year and end_date in ['present', 'current', 'now']:
                    print(f"[EXPERIENCE EXTRACT] Allowing future start year with 'present' end: {start_date} - {end_date} (might be typo or current job)")
            
            # Clean context to remove personal contact information
            context = _clean_experience_context(context)
            
            # Log the context for debugging
            print(f"[EXPERIENCE EXTRACT] Processing date range: {start_date} - {end_date}")
            # Safely print context preview (handle Unicode characters)
            try:
                safe_context = context[:200].encode('ascii', errors='replace').decode('ascii')
                print(f"[EXPERIENCE EXTRACT] Context preview: {safe_context}...")
            except Exception:
                print(f"[EXPERIENCE EXTRACT] Context preview: [contains non-ASCII characters, length: {len(context[:200])}]")
            
            # Additional filtering: ensure this looks like work experience
            # BUT: be less strict - if we have a date range, assume it's experience unless clearly not
            looks_like_work = _looks_like_work_experience(context)
            print(f"[EXPERIENCE EXTRACT] Looks like work experience: {looks_like_work}")
            
            # Try to extract job title, company, and responsibilities
            job_title = _extract_job_title_from_context(context)
            company = _extract_company_from_context(context)
            responsibilities = _extract_responsibilities_from_context(context)
            achievements = _extract_achievements_from_context(context)
            
            print(f"[EXPERIENCE EXTRACT] Extracted: title='{job_title}', company='{company}'")
            
            # If we have a date range but filters are too strict, try a more lenient approach
            # Look for company names near the date range even if _looks_like_work_experience is False
            if not company and not job_title:
                # Try to extract company name more aggressively from lines near the date
                lines = context.split('\n')
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    # Look for capitalized words that might be company names
                    if len(line_clean) > 3 and line_clean[0].isupper():
                        # Check if it's not a common word
                        if not any(word in line_clean.lower() for word in ['phone', 'email', 'contact', 'address', 'location', 'project', 'projects']):
                            # Check if there's a date nearby
                            if any(date_str in context[max(0, i-3):i+3] for date_str in [start_date, end_date]):
                                company = line_clean
                                print(f"[EXPERIENCE EXTRACT] Found company from nearby line: {company}")
                                break
            
            # LENIENT: If we have valid dates, try hard to find company/title, but don't skip if we have dates
            # Valid dates are a strong signal of experience, even without company/title
            if not job_title and not company:
                # Last resort: try to get company from line before the date
                date_line_start = context.find(start_date)
                if date_line_start > 0:
                    # Look backwards for company name
                    before_date = context[:date_line_start].strip()
                    lines_before = before_date.split('\n')
                    for line in reversed(lines_before[-5:]):  # Check last 5 lines before date (increased)
                        line_clean = line.strip()
                        if len(line_clean) > 2 and line_clean[0].isupper() and len(line_clean.split()) <= 8:
                            if not any(word in line_clean.lower() for word in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'present', 'current', 'phone', 'email', 'contact']):
                                company = line_clean
                                print(f"[EXPERIENCE EXTRACT] Found company from line before date: {company}")
                                break
                
                # If still no company, try looking in lines after the date too
                if not company:
                    date_line_end = context.find(end_date if end_date != 'present' else start_date, date_line_start if date_line_start > 0 else 0)
                    if date_line_end > 0:
                        after_date = context[date_line_end + len(end_date):date_line_end + 200].strip()
                        lines_after = after_date.split('\n')
                        for line in lines_after[:3]:  # Check first 3 lines after date
                            line_clean = line.strip()
                            if len(line_clean) > 2 and line_clean[0].isupper() and len(line_clean.split()) <= 8:
                                if not any(word in line_clean.lower() for word in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'present', 'current']):
                                    company = line_clean
                                    print(f"[EXPERIENCE EXTRACT] Found company from line after date: {company}")
                                    break
            
            # LENIENT: If we have valid dates but no company/title, still create entry (dates are valuable)
            # Only skip if we're very confident it's NOT experience (e.g., education section)
            if not company and not job_title:
                # Check if context clearly indicates it's NOT work experience
                context_lower = context.lower()
                non_work_indicators = ['education', 'degree', 'university', 'college', 'school', 'graduated', 'expected', 'coursework']
                if any(indicator in context_lower for indicator in non_work_indicators):
                    print(f"[EXPERIENCE EXTRACT] Skipping - dates found but context suggests education/non-work")
                    continue
                else:
                    # We have valid dates and it's not clearly education - create entry with unknown company/title
                    print(f"[EXPERIENCE EXTRACT] Creating entry with valid dates but no company/title (dates are strong signal)")
            
            # Filter out obviously wrong companies (like "My projects", education sections, etc.)
            invalid_company_patterns = [
                'my project', 'projects', 'experience with', 'experience in',
                'skills', 'languages', 'frameworks', 'tools', 'technologies',
                'education', 'degree', 'university', 'college', 'school',
                'expected', 'graduation', 'coursework', 'certificate',
                'nce in', 'erience in', 'developing and deploying',  # Common context window artifacts
                'digital ocean', 'aws', 's3', 'mongodb', 'mysql',  # These are technologies, not companies
                'react', 'node.js', 'express', 'python', 'javascript',  # Technologies
                'pytest', 'power bi', 'tableau', 'power bi table',  # Tools
                'indore expected', 'expected 2026', 'higher secondary', 'secondary school',  # Education artifacts
                'indore', 'india',  # Location names (often confused with companies)
                'operating', 'systems', 'data structures', 'algorithms',  # Coursework/education terms
            ]
            
            # Also filter titles that are clearly not job titles
            invalid_title_patterns = [
                'pytest', 'power bi', 'tableau', 'digital ocean', 'aws', 's3',
                'mongodb', 'mysql', 'react', 'node.js', 'express', 'python',
                'javascript', 'indore', 'expected', 'secondary', 'higher',
                'school', 'university', 'college', 'ps using', 'and digital',
                'operating', 'systems', 'data structures', 'algorithms',  # Coursework
            ]
            
            title_lower = job_title.lower() if job_title else ""
            if job_title and any(pattern in title_lower for pattern in invalid_title_patterns):
                print(f"[EXPERIENCE EXTRACT] Filtering out invalid title (looks like tool/technology/coursework): {job_title}")
                job_title = ""
            
            company_lower = company.lower() if company else ""
            if company and any(pattern in company_lower for pattern in invalid_company_patterns):
                print(f"[EXPERIENCE EXTRACT] Filtering out invalid company name: {company}")
                company = ""  # Clear it and try to find another
            
            # STRICT: Reject entries where company/title are clearly invalid (single generic words, course names, etc.)
            # Single word companies that are common words are likely false positives
            common_words_as_companies = ['operating', 'systems', 'data', 'science', 'intern', 'development', 
                                         'management', 'system', 'algorithm', 'structure', 'programming',
                                         'network', 'database', 'object', 'oriented', 'communication']
            if company and len(company.split()) == 1 and company.lower() in common_words_as_companies:
                print(f"[EXPERIENCE EXTRACT] Rejecting single-word common word as company: {company}")
                company = ""
            
            # STRICT: If company is same as title, it's likely a mistake (title extracted as company)
            if company and job_title and company.lower() == job_title.lower():
                print(f"[EXPERIENCE EXTRACT] Rejecting entry where company equals title (likely extraction error): {company}")
                company = ""
            
            # Also filter if company name is too long (likely picked up entire context)
            if company and len(company) > 60:
                print(f"[EXPERIENCE EXTRACT] Filtering out company name that's too long (likely context artifact): {company[:50]}...")
                company = ""
            
            # Filter if company name contains numbers in wrong places (like "Expected 2026 2022")
            if company and re.search(r'\d{4}\s+\d{4}', company):
                print(f"[EXPERIENCE EXTRACT] Filtering out company with multiple years (likely education): {company}")
                company = ""
            
            # LENIENT: Valid dates are strong evidence of experience - don't skip just because company/title missing
            # Only skip if we're very confident it's NOT experience (already checked above)
            # The check above already handles this - if we reach here, we're creating the entry
            
            # Calculate years of experience for this entry
            years_in_role = _calculate_years_for_single_entry(start_date, end_date)
            
            # Create simplified experience entry - show only years, not company/title details
            # This avoids showing inaccurate extraction results like "Technical Skills & Platforms Tools"
            experience_entry = {
                "title": "Work Experience",  # Generic title instead of extracted (often inaccurate)
                "position": "Work Experience", 
                "company": "",  # Empty company - not showing inaccurate extractions
                "duration": f"{start_date} - {end_date}",
                "years": round(years_in_role, 1),  # Years of experience for this role
                "years_display": f"{round(years_in_role, 1)} years" if years_in_role >= 1 else f"{round(years_in_role * 12, 1)} months",
                "start_date": start_date,
                "end_date": end_date,
                "description": "",  # Not showing description to avoid inaccurate extractions
                "responsibilities": [],
                "achievements": []
            }
            
            experiences.append(experience_entry)
            print(f"[EXPERIENCE EXTRACT] Added entry: {company or 'Unknown'} - {job_title or 'Unknown'} ({start_date} - {end_date})")
        
        print(f"[EXPERIENCE EXTRACT] Primary extraction found {len(experiences)} entries")
        
        # Secondary regex pass to catch formats like "Title at Company (Dates)" or "Company - Title (Dates)"
        # This is important for resumes that list experiences in structured formats
        secondary_patterns = [
            # "Software Engineer at ABC Corp Jan 2022 - May 2024"
            r"(?P<title>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\s+at\s+(?P<company>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\s+(?P<start>(?:\w+\s+)?(?:19\d{2}|20\d{2}))\s*[-–]\s*(?P<end>(?:\w+\s+)?(?:19\d{2}|20\d{2}|present|current))",
            # "ABC Corp - Software Engineer (Jan 2022 - May 2024)"
            r"(?P<company>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\s+[-–]\s+(?P<title>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\s*\((?P<start>(?:\w+\s+)?(?:19\d{2}|20\d{2}))\s*[-–]\s*(?P<end>(?:\w+\s+)?(?:19\d{2}|20\d{2}|present|current))\)",
            # "Company Name\nTitle\nJan 2022 - May 2024" (multiline format)
            r"(?P<company>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\n(?P<title>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\n(?P<start>(?:\w+\s+)?(?:19\d{2}|20\d{2}))\s*[-–]\s*(?P<end>(?:\w+\s+)?(?:19\d{2}|20\d{2}|present|current))",
            # "Title\nCompany Name\nJan 2022 - May 2024" (multiline format)
            r"(?P<title>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\n(?P<company>[A-Z][a-zA-Z\s&/.\-]{2,60}?)\n(?P<start>(?:\w+\s+)?(?:19\d{2}|20\d{2}))\s*[-–]\s*(?P<end>(?:\w+\s+)?(?:19\d{2}|20\d{2}|present|current))",
        ]

        print(f"[EXPERIENCE EXTRACT] Running secondary pattern matching on {'experience section(s)' if experience_sections else 'full text'}")
        for sp in secondary_patterns:
            for m in re.finditer(sp, search_text, re.IGNORECASE | re.MULTILINE):
                title = m.group('title').strip()
                company = m.group('company').strip()
                start_date = m.group('start').strip()
                end_date = m.group('end').strip().lower()
                
                # Validate dates
                if not _is_valid_date_range(start_date, end_date):
                    continue
                
                # Skip if looks like education
                # Map match position back to original resume_text
                match_start_in_search = m.start()
                if experience_sections:
                    # Find which section this match belongs to
                    cumulative_pos = 0
                    match_start = m.start()
                    for start, end, header in experience_sections:
                        section_len = end - start
                        if match_start_in_search < cumulative_pos + section_len:
                            match_start = start + (match_start_in_search - cumulative_pos)
                            break
                        cumulative_pos += section_len + 1
                else:
                    match_start = m.start()
                section_start = resume_text.rfind('\n', 0, match_start)
                section_text = resume_text[max(0, section_start-150):match_start].lower()
                if any(edu_word in section_text for edu_word in ['education', 'degree', 'bachelor', 'master', 'phd']):
                    continue

                print(f"[EXPERIENCE EXTRACT] Secondary pattern found: {company} - {title} ({start_date} - {end_date})")
                
                # Calculate years for this entry
                years_in_role = _calculate_years_for_single_entry(start_date, end_date)

                # Create experience entry preserving company/title and readable duration
                experience_entry = {
                    "title": title or "Unknown",
                    "position": title or "Unknown",
                    "company": company or "Unknown",
                    "duration": f"{start_date} - {end_date}",
                    "years": round(years_in_role, 1),
                    "years_display": f"{round(years_in_role, 1)} years" if years_in_role >= 1 else f"{round(years_in_role * 12, 1)} months",
                    "start_date": start_date,
                    "end_date": end_date,
                    "description": resume_text[max(0, match_start-120):match_start+200].strip(),
                    "responsibilities": [],
                    "achievements": []
                }
                experiences.append(experience_entry)

        print(f"[EXPERIENCE EXTRACT] Before deduplication: {len(experiences)} entries")
        
        # Remove duplicates - be more conservative: only remove if SAME company AND SAME dates
        # Different companies should NEVER be considered duplicates
        unique_experiences = []
        seen_keys = []
        
        def normalize_company_name(company: str) -> str:
            """Normalize company name for comparison"""
            if not company or company == "Unknown Company":
                return ""
            # Lowercase, remove common words, normalize whitespace
            normalized = company.lower().strip()
            normalized = re.sub(r'\s+', ' ', normalized)
            # Remove common suffixes that might vary
            normalized = re.sub(r'\s+(inc|llc|ltd|corp|corporation|company|technologies|tech|solutions|services)$', '', normalized)
            return normalized
        
        def extract_year(date_str):
            """Extract year from date string"""
            if not date_str:
                return None
            date_str = str(date_str).strip()
            if date_str.lower() in ['present', 'current', 'now']:
                return 'present'
            # Try to find 4-digit year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
            if year_match:
                return year_match.group(1)
            return date_str
        
        for exp in experiences:
            company = exp.get("company", "")
            title = exp.get("title", "") or exp.get("position", "")
            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", "").lower()
            
            # Skip if both are defaults/unknown
            if (company == "Unknown Company" and title == "Unknown Position"):
                print(f"[EXPERIENCE EXTRACT] Skipping entry with no company/title info")
                continue
            
            start_year = extract_year(start_date)
            end_year = extract_year(end_date)
            
            # Normalize company name for comparison
            normalized_company = normalize_company_name(company)
            
            # Create key: (normalized_company, start_year, end_year)
            # Only consider duplicate if same company AND same dates
            key = (normalized_company, start_year, end_year)
            
            # LENIENT deduplication: Only consider duplicate if SAME company AND same dates
            # Different companies with same dates should be kept (e.g., contractor work)
            is_duplicate = False
            date_range_key = (start_year, end_year)
            
            # Check if we've already seen this exact date range WITH THE SAME COMPANY
            # If different company, it's a different experience even with same dates
            existing_entry_idx = None
            for idx, seen_key in enumerate(seen_keys):
                seen_norm_company, seen_sy, seen_ey = seen_key
                # Only consider duplicate if BOTH dates AND company match
                if start_year == seen_sy and end_year == seen_ey:
                    # Check if company also matches (normalized)
                    if normalized_company and seen_norm_company and normalized_company == seen_norm_company:
                        existing_entry_idx = idx
                        break
                    # If dates match but company is different, it's NOT a duplicate - keep both
                    elif normalized_company and seen_norm_company and normalized_company != seen_norm_company:
                        print(f"[EXPERIENCE EXTRACT] Same dates ({start_year}-{end_year}) but different companies: '{normalized_company}' vs '{seen_norm_company}' - keeping both")
                        # Don't break - continue to check other entries
                    # If both have no company info, might be duplicate - check further
                    elif not normalized_company and not seen_norm_company:
                        # Same dates, both unknown companies - might be duplicate, but be lenient
                        # Only mark as duplicate if positions are very close (handled by position check in pattern matching)
                        pass
            
            if existing_entry_idx is not None:
                # We have the same dates - check if we should keep the new one or the existing one
                existing_exp = unique_experiences[existing_entry_idx]
                existing_company = existing_exp.get("company", "").strip()
                existing_title = existing_exp.get("title", "").strip()
                
                # Score entries: better entry has valid company AND valid title
                current_score = 0
                existing_score = 0
                
                # Score current entry
                if company and company != "Unknown Company" and len(company.split()) > 1:
                    current_score += 2
                elif company and company != "Unknown Company":
                    current_score += 1
                if title and title != "Unknown Position" and len(title.split()) > 1:
                    current_score += 2
                elif title and title != "Unknown Position":
                    current_score += 1
                
                # Score existing entry
                if existing_company and existing_company != "Unknown Company" and len(existing_company.split()) > 1:
                    existing_score += 2
                elif existing_company and existing_company != "Unknown Company":
                    existing_score += 1
                if existing_title and existing_title != "Unknown Position" and len(existing_title.split()) > 1:
                    existing_score += 2
                elif existing_title and existing_title != "Unknown Position":
                    existing_score += 1
                
                # If current entry is better, replace the existing one
                if current_score > existing_score:
                    print(f"[EXPERIENCE EXTRACT] Replacing duplicate entry (same dates {start_year}-{end_year}): '{existing_company}/{existing_title}' (score: {existing_score}) with '{company}/{title}' (score: {current_score})")
                    unique_experiences[existing_entry_idx] = exp
                    seen_keys[existing_entry_idx] = key
                    is_duplicate = True  # Mark as duplicate so we don't add it again
                else:
                    is_duplicate = True
                    print(f"[EXPERIENCE EXTRACT] Skipping duplicate (same dates {start_year}-{end_year}): '{company}/{title}' (score: {current_score}) - keeping existing '{existing_company}/{existing_title}' (score: {existing_score})")
            else:
                # No existing entry with same dates - check for exact key match
                if key in seen_keys:
                    is_duplicate = True
                    print(f"[EXPERIENCE EXTRACT] Skipping duplicate (exact key match): {company} ({start_year}-{end_year})")
                else:
                    # Check for same normalized company with same dates
                    for seen_key in seen_keys:
                        seen_norm_company, seen_sy, seen_ey = seen_key
                        if normalized_company and seen_norm_company and normalized_company == seen_norm_company:
                            if start_year == seen_sy and end_year == seen_ey:
                                is_duplicate = True
                                print(f"[EXPERIENCE EXTRACT] Skipping duplicate (same company '{company}', same dates {start_year}-{end_year})")
                                break
            
            if not is_duplicate:
                unique_experiences.append(exp)
                seen_keys.append(key)
                print(f"[EXPERIENCE EXTRACT] Added unique entry: {company or 'Unknown'} ({title or 'Unknown'}) | {start_year}-{end_year}")
        
        print(f"[EXPERIENCE EXTRACT] After deduplication: {len(unique_experiences)} unique entries")
        
        # Sort by start date (most recent first)
        def get_sort_year(exp):
            """Extract year for sorting"""
            start_date = exp.get("start_date", "")
            if not start_date:
                return 0
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', str(start_date))
            if year_match:
                return int(year_match.group(1))
            return 0
        
        try:
            unique_experiences.sort(key=get_sort_year, reverse=True)
        except:
            pass  # If sorting fails, keep original order
        
        final_experiences = unique_experiences[:5]  # Limit to 5 most recent experiences
        print(f"[EXPERIENCE EXTRACT] Final result: {len(final_experiences)} experience entries")
        return final_experiences
        
    except Exception as e:
        print(f"[EXPERIENCE EXTRACT] ERROR: spaCy experience extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_education_with_spacy(resume_text: str) -> List[Dict[str, Any]]:
    """Extract education using spaCy NLP"""
    try:
        nlp = _get_spacy_model()
        if nlp is None:
            return []
        
        doc = nlp(resume_text)
        education = []
        
        # Look for education patterns with more comprehensive matching
        education_patterns = [
            r'(bachelor|master|phd|doctorate|diploma|certificate|degree)\s+(?:of|in|in\s+science|in\s+arts|in\s+engineering|in\s+computer|in\s+technology)',
            r'(b\.?s\.?|m\.?s\.?|ph\.?d\.?|mba|b\.?tech|m\.?tech)\s+(?:in|of)',
            r'(university|college|institute|school)\s+of',
            r'(bachelor|master|phd|doctorate|diploma|certificate|degree)',
            r'(b\.?s\.?|m\.?s\.?|ph\.?d\.?|mba|b\.?tech|m\.?tech)',
        ]
        
        for pattern in education_patterns:
            matches = re.finditer(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                # Extract text around the match for context
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(resume_text), match.end() + 100)
                context = resume_text[start_pos:end_pos]
                
                # Try to extract degree, institution, field, and graduation year
                degree = _extract_degree_from_context(context)
                institution = _extract_institution_from_context(context)
                field = _extract_field_from_context(context)
                graduation_year = _extract_graduation_year_from_context(context)
                gpa = _extract_gpa_from_context(context)
                
                if degree or institution:
                    education.append({
                        "degree": degree,
                        "institution": institution,
                        "field": field,
                        "graduation_year": graduation_year,
                        "gpa": gpa,
                        "full_education": _extract_full_education_from_context(context)
                    })
        
        # Remove duplicates and sort by graduation year
        unique_education = []
        seen = set()
        for edu in education:
            # Create a more specific key to avoid duplicates
            degree = edu.get("degree", "").lower()
            institution = edu.get("institution", "").lower()
            field = edu.get("field", "").lower()
            
            # Skip if degree or institution is too generic
            if degree in ["", "bachelor", "master", "phd"] and institution == "":
                continue
                
            key = (degree, institution, field)
            if key not in seen and key != ("", "", ""):
                unique_education.append(edu)
                seen.add(key)
        
        return unique_education[:3]  # Limit to 3 most relevant education entries
        
    except Exception as e:
        print(f"spaCy education extraction error: {e}")
        return []

def _extract_job_title_from_context(context: str) -> str:
    """Extract job title from experience context"""
    # Look for job titles in various formats
    job_patterns = [
        r'(\w+\s+\w+\s+&\s+\w+\s+\w+)',  # "Web Designer & SEO Specialist"
        r'(\w+\s+\w+\s+\w+)',  # "Senior Software Engineer"
        r'(\w+\s+\w+)',  # "Software Engineer"
        r'(software engineer|developer|programmer|analyst|manager|director|lead|senior|junior)',
        r'(engineer|developer|analyst|manager|director|lead|senior|junior)\s+\w+',
        r'(\w+\s+engineer|\w+\s+developer|\w+\s+analyst|\w+\s+manager)',
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            
            # Filter out personal information and non-job titles
            if any(word in title.lower() for word in ['phone', 'email', 'contact', 'address', 'location', 'www', 'http']):
                continue
            
            # Filter out common non-job words
            if any(word in title.lower() for word in ['optimized', 'pages', 'leading', 'traffic', 'increase', 'designed', 'responsive']):
                continue
                
            # Clean up the title
            title = re.sub(r'\s+', ' ', title)  # Remove extra spaces
            return title.title()
    
    return ""

def _extract_company_from_context(context: str) -> str:
    """Extract company name from experience context"""
    # Look for company indicators with more patterns
    company_patterns = [
        r'at\s+([A-Z][a-zA-Z0-9\s&./\-]+?)(?:\s+as|\s+\d|\s*[,\n]|\s*$|\.)',
        r'([A-Z][a-zA-Z0-9\s&./\-]+?)\s+as\s+\w+',
        r'worked\s+at\s+([A-Z][a-zA-Z0-9\s&./\-]+?)(?:\s+as|\s+\d|\s*[,\n]|\s*$|\.)',
        r'([A-Z][a-zA-Z0-9\s&./\-]+?)\s+(?:Inc|Corp|LLC|Ltd|Company|Solutions|Technologies|Systems|Services|Group|Industries)',
        r'company[:\s]+([A-Z][a-zA-Z0-9\s&./\-]+?)(?:\s+as|\s+\d|\s*[,\n]|\s*$|\.)',
        # Look for capitalized words/phrases that might be company names
        r'\n([A-Z][a-zA-Z0-9\s&./\-]{3,50}?)\s*\n(?=.*\d{4})',  # Company name on its own line followed by a year
    ]
    
    for pattern in company_patterns:
        matches = re.finditer(pattern, context, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            company = match.group(1).strip()
            
            # Filter out personal information and non-company names
            if any(word in company.lower() for word in ['phone', 'email', 'contact', 'address', 'location', 'www', 'http', 'gmail', 'yahoo', 'hotmail', 'linkedin', 'github']):
                continue
            
            # Filter out common non-company words (but be less aggressive)
            invalid_words = ['optimized', 'pages', 'leading', 'traffic', 'increase', 'designed', 'responsive', 
                           'freelancer', 'my project', 'projects', 'experience with', 'experience in',
                           'responsible for', 'worked on', 'developed', 'created', 'built']
            if any(word in company.lower() for word in invalid_words):
                continue
            
            # Filter out if it's just a date or month
            if re.match(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}$', company, re.IGNORECASE):
                continue
            
            # Filter out if it's too short or too long
            if len(company) < 2 or len(company) > 100:
                continue
                
            # Clean up the company name
            company = re.sub(r'\s+', ' ', company)  # Remove extra spaces
            company = company.strip('.,;:()[]{}')
            
            # If we found a reasonable company name, return it
            if len(company) >= 2:
                return company
    
    # Additional: Look for company names on lines before dates
    # Split context into lines and look for patterns
    lines = context.split('\n')
    for i, line in enumerate(lines):
        line_clean = line.strip()
        # Look for lines that start with capital letter and might be company names
        if line_clean and line_clean[0].isupper() and len(line_clean.split()) <= 6:
            # Check if next lines have dates
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line has a date or year, this might be a company
                if re.search(r'\d{4}', next_line):
                    # Check it's not a common invalid word
                    if not any(word in line_clean.lower() for word in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'present', 'current', 'phone', 'email']):
                        if len(line_clean) >= 2:
                            return line_clean
    
    return ""

def _extract_degree_from_context(context: str) -> str:
    """Extract degree from education context"""
    degree_patterns = [
        r'(bachelor|master|phd|doctorate|diploma|certificate|degree)',
        r'(b\.?s\.?|m\.?s\.?|ph\.?d\.?|mba|b\.?tech|m\.?tech)',
    ]
    
    for pattern in degree_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return ""

def _extract_institution_from_context(context: str) -> str:
    """Extract institution from education context"""
    institution_patterns = [
        r'(university|college|institute|school)\s+of\s+([A-Z][a-zA-Z\s&]+)',
        r'([A-Z][a-zA-Z\s&]+)\s+(university|college|institute)',
    ]
    
    for pattern in institution_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return ""

def _extract_field_from_context(context: str) -> str:
    """Extract field of study from education context"""
    field_patterns = [
        r'(?:in|of)\s+(computer science|engineering|technology|business|arts|science)',
        r'(computer science|engineering|technology|business|arts|science)',
    ]
    
    for pattern in field_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(1).title()
    
    return ""

def _extract_responsibilities_from_context(context: str) -> List[str]:
    """Extract job responsibilities from experience context"""
    responsibilities = []
    
    # Look for bullet points or responsibility indicators
    responsibility_patterns = [
        r'•\s*([^•\n]+)',
        r'-\s*([^-\n]+)',
        r'\*\s*([^*\n]+)',
        r'Responsible for\s*([^.\n]+)',
        r'Duties include\s*([^.\n]+)',
    ]
    
    for pattern in responsibility_patterns:
        matches = re.finditer(pattern, context, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            responsibility = match.group(1).strip()
            
            # Filter out personal information
            if any(word in responsibility.lower() for word in ['phone', 'email', 'contact', 'address', 'location', 'www', 'http', 'gmail', 'yahoo', 'hotmail']):
                continue
                
            if len(responsibility) > 10 and len(responsibility) < 200:  # Reasonable length
                responsibilities.append(responsibility)
    
    return responsibilities[:5]  # Limit to 5 responsibilities

def _extract_achievements_from_context(context: str) -> List[str]:
    """Extract achievements from experience context"""
    achievements = []
    
    # Look for achievement indicators
    achievement_patterns = [
        r'achieved\s*([^.\n]+)',
        r'increased\s*([^.\n]+)',
        r'improved\s*([^.\n]+)',
        r'reduced\s*([^.\n]+)',
        r'led\s*([^.\n]+)',
        r'managed\s*([^.\n]+)',
        r'developed\s*([^.\n]+)',
        r'created\s*([^.\n]+)',
        r'built\s*([^.\n]+)',
        r'designed\s*([^.\n]+)',
    ]
    
    for pattern in achievement_patterns:
        matches = re.finditer(pattern, context, re.IGNORECASE)
        for match in matches:
            achievement = match.group(1).strip()
            if len(achievement) > 10 and len(achievement) < 200:  # Reasonable length
                achievements.append(achievement)
    
    return achievements[:3]  # Limit to 3 achievements

def _extract_graduation_year_from_context(context: str) -> str:
    """Extract graduation year from education context"""
    year_patterns = [
        r'(\d{4})',
        r'graduated\s+in\s+(\d{4})',
        r'completed\s+in\s+(\d{4})',
        r'(\d{4})\s*graduate',
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            year = match.group(1)
            # Validate year (should be reasonable graduation year)
            if 1950 <= int(year) <= 2030:
                return year
    
    return ""

def _extract_gpa_from_context(context: str) -> str:
    """Extract GPA from education context"""
    gpa_patterns = [
        r'gpa[:\s]*(\d+\.?\d*)',
        r'grade[:\s]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*gpa',
        r'(\d+\.?\d*)\s*out\s+of\s+4',
    ]
    
    for pattern in gpa_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            gpa = match.group(1)
            # Validate GPA (should be reasonable)
            try:
                gpa_val = float(gpa)
                if 0.0 <= gpa_val <= 4.0:
                    return gpa
            except ValueError:
                continue
    
    return ""

def _extract_full_education_from_context(context: str) -> str:
    """Extract full education line from context"""
    # Clean up the context and return the most relevant part
    lines = context.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) > 10 and any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'university', 'college']):
            return line
    
    return context.strip()

def _calculate_experience_years_from_entries(experience_entries: List[Dict[str, Any]], resume_text: str) -> float:
    """Calculate total years of experience from actual experience entries"""
    try:
        total_years = 0.0
        
        print(f"[EXPERIENCE CALC] Starting calculation with {len(experience_entries) if experience_entries else 0} experience entries")
        
        # Helpers for normalization and overlap
        def _canonical(text: str) -> str:
            if not text:
                return ""
            t = text.lower()
            # Remove common filler words that leak from context windows
            stop = set([
                "background", "strong", "experience", "with", "in", "on", "and", "for", "team", "tech",
                "working", "building", "role", "project", "projects", "responsible", "as"
            ])
            t = re.sub(r"[^a-z0-9&./\-\s]", " ", t)
            words = [w for w in re.split(r"\s+", t) if w and w not in stop and len(w) > 1]
            return " ".join(words)[:80]

        def _ranges_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
            try:
                def year_of(d: str) -> int:
                    if not d:
                        return 0
                    m = re.search(r"(19\d{2}|20\d{2})", d)
                    return int(m.group(1)) if m else 0
                asy, aey = year_of(a_start), year_of(a_end)
                bsy, bey = year_of(b_start), year_of(b_end)
                if not asy or not aey or not bsy or not bey:
                    return False
                return not (aey < bsy or bey < asy)
            except:
                return False

        # STRICT deduplication: If same dates, keep only ONE entry (the best one)
        # This prevents the same experience from being counted multiple times
        unique_entries = []
        seen_date_ranges = {}  # Map: (start_year, end_year) -> best_entry
        
        # Helper to score an entry's completeness (better = valid company + valid title)
        def score_entry(exp):
            company = exp.get("company", "").strip()
            title = exp.get("title", "") or exp.get("position", "")
            title = title.strip() if title else ""
            score = 0
            if company and company != "Unknown Company":
                if len(company.split()) > 1:
                    score += 3  # Multi-word company is more reliable
                else:
                    score += 1  # Single word might be valid
            if title and title != "Unknown Position":
                if len(title.split()) > 1:
                    score += 3  # Multi-word title is more reliable
                else:
                    score += 1  # Single word might be valid
            return score
        
        def normalize_company_for_calc(company: str) -> str:
            """Normalize company name for duplicate detection with better fuzzy matching"""
            if not company or company == "Unknown Company":
                return ""
            
            # Lowercase, normalize
            normalized = company.lower().strip()
            normalized = re.sub(r'\s+', ' ', normalized)
            
            # Remove common suffixes that might vary
            normalized = re.sub(r'\s+(inc|llc|ltd|corp|corporation|company|technologies|tech|solutions|services|systems)$', '', normalized)
            
            # Remove special characters for better matching
            normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
            
            # Remove common filler words that appear in context windows
            filler_words = ['nce', 'erience', 'experi', 'experience', 'with', 'in', 'developing', 'deploying', 
                          'end-to-end', 'ai', 'solutions', 'skilled', 'python', 'fastapi', 'transformer',
                          'based', 'architectures', 'automation', 'recommendation', 'nlp-based', 'applications',
                          'strong', 'background', 'building', 'and', 'the', 'a', 'an', 'for', 'to', 'of']
            words = normalized.split()
            words = [w for w in words if w not in filler_words and len(w) > 2]
            
            # If the normalized company is mostly filler words or very short, it's likely invalid
            if len(words) < 2:
                return ""
            
            # Take core words (first 2-4 meaningful words)
            if len(words) > 4:
                normalized = ' '.join(words[:4])
            else:
                normalized = ' '.join(words)
            
            return normalized
        
        def extract_year_from_date(date_str):
            """Extract year from date string, handling various formats"""
            if not date_str:
                return None
            date_str = str(date_str).strip()
            if date_str.lower() in ['present', 'current', 'now']:
                return 'present'
            # Find 4-digit year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
            if year_match:
                return year_match.group(1)
            return None
        
        for exp in experience_entries:
            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", "").lower()
            company = exp.get("company", "").strip()
            title = (exp.get("title", "") or exp.get("position", "")).strip()
            start_year = extract_year_from_date(start_date)
            end_year = extract_year_from_date(end_date)
            
            if not start_year or not end_year:
                # Can't deduplicate without years, just add it
                unique_entries.append(exp)
                print(f"[EXPERIENCE CALC] Added entry (no dates): {company}")
                continue
            
            # STRICT: If same dates, keep only the BEST entry (most complete company/title)
            date_key = (start_year, end_year)
            
            if date_key in seen_date_ranges:
                # We've seen these dates before - compare and keep the better one
                existing_entry = seen_date_ranges[date_key]
                existing_score = score_entry(existing_entry)
                current_score = score_entry(exp)
                
                if current_score > existing_score:
                    print(f"[EXPERIENCE CALC] Replacing entry with same dates ({start_year}-{end_year}): '{existing_entry.get('company', 'Unknown')}/{existing_entry.get('title', 'Unknown')}' (score: {existing_score}) -> '{company}/{title}' (score: {current_score})")
                    seen_date_ranges[date_key] = exp
                else:
                    print(f"[EXPERIENCE CALC] Skipping duplicate dates ({start_year}-{end_year}): '{company}/{title}' (score: {current_score}) - keeping better entry '{existing_entry.get('company', 'Unknown')}/{existing_entry.get('title', 'Unknown')}' (score: {existing_score})")
            else:
                # First time seeing these dates - add it
                seen_date_ranges[date_key] = exp
                print(f"[EXPERIENCE CALC] Added entry with dates ({start_year}-{end_year}): '{company or 'Unknown'}/{title or 'Unknown'}'")
        
        # Convert seen_date_ranges to list for calculation
        unique_entries = list(seen_date_ranges.values())
        print(f"[EXPERIENCE CALC] After date-based deduplication: {len(unique_entries)} unique entries")
        
        # Use unique entries for calculation
        experience_entries = unique_entries
        
        # Calculate from experience entries
        if experience_entries and len(experience_entries) > 0:
            from datetime import datetime
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            for idx, exp in enumerate(experience_entries):
                start_date = exp.get("start_date", "")
                end_date = exp.get("end_date", "").lower()
                duration = exp.get("duration", "")
                
                print(f"[EXPERIENCE CALC] Entry {idx+1}: start_date='{start_date}', end_date='{end_date}', duration='{duration}'")
                
                # Try to extract from duration string if dates are missing
                if not start_date and duration:
                    # Try to parse duration like "2020 - 2023" or "Jan 2020 - Present"
                    duration_match = re.search(r'(\d{4}|\w+\s+\d{4})\s*[-–]\s*(\d{4}|\w+\s+\d{4}|present|current)', duration, re.IGNORECASE)
                    if duration_match:
                        start_date = duration_match.group(1).strip()
                        end_date = duration_match.group(2).strip().lower()
                        print(f"[EXPERIENCE CALC] Parsed from duration: '{start_date}' to '{end_date}'")
                
                if not start_date:
                    print(f"[EXPERIENCE CALC] Skipping entry {idx+1}: no start_date")
                    continue
                
                try:
                    start_year = None
                    start_month = 1
                    end_year = None
                    end_month = 1
                    
                    # Parse start date - more flexible (handles month-year and year-only)
                    start_date_clean = str(start_date).strip()
                    
                    # Month name mapping
                    month_map = {
                        'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
                        'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
                        'may': 5, 'jun': 6, 'june': 6,
                        'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
                        'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
                        'nov': 11, 'november': 11, 'dec': 12, 'december': 12
                    }
                    
                    if ' ' in start_date_clean:  # Month Year format like "Jan 2020" or "January 2020"
                        parts = start_date_clean.split()
                        # Find the year (4-digit number)
                        for part in parts:
                            if part.isdigit() and len(part) == 4:
                                start_year = int(part)
                                break
                        if start_year is None and len(parts) >= 2:
                            # Try last part as year
                            if parts[-1].isdigit():
                                start_year = int(parts[-1])
                        
                        # Try to extract month from start date
                        for part in parts:
                            part_lower = part.lower()
                            if part_lower in month_map:
                                start_month = month_map[part_lower]
                                break
                    else:  # Year only
                        if start_date_clean.isdigit():
                            start_year = int(start_date_clean)
                        elif len(start_date_clean) == 4:  # "2020"
                            start_year = int(start_date_clean)
                    
                    if start_year is None or not (1950 <= start_year <= 2030):
                        print(f"[EXPERIENCE CALC] Invalid start_year: {start_year}")
                        continue
                    
                    # Parse end date - more flexible (handles month-year, year-only, and "present")
                    if end_date in ['present', 'current', 'now']:
                        end_year = current_year
                        end_month = current_month
                    elif ' ' in end_date:  # Month Year format like "Dec 2023" or "December 2023"
                        parts = end_date.split()
                        for part in parts:
                            if part.isdigit() and len(part) == 4:
                                end_year = int(part)
                                break
                        if end_year is None and len(parts) >= 2:
                            if parts[-1].isdigit():
                                end_year = int(parts[-1])
                        
                        # Try to extract month from end date
                        for part in parts:
                            part_lower = part.lower()
                            if part_lower in month_map:
                                end_month = month_map[part_lower]
                                break
                    else:  # Year only
                        if end_date.isdigit():
                            end_year = int(end_date)
                        elif len(end_date) == 4:
                            end_year = int(end_date)
                    
                    if end_year is None or not (1950 <= end_year <= 2030):
                        print(f"[EXPERIENCE CALC] Invalid end_year: {end_year}")
                        continue
                    
                    # Validate date logic
                    if end_year < start_year:
                        print(f"[EXPERIENCE CALC] Invalid date range: {start_year} to {end_year}")
                        continue
                    
                    # STRICT: Filter out future dates (start date after current year)
                    if start_year > current_year:
                        print(f"[EXPERIENCE CALC] Skipping entry with future start date: {start_year} (current: {current_year})")
                        continue
                    
                    # STRICT: Filter out end dates that are in the future
                    # If end_year is greater than current_year, it's definitely in the future
                    if end_year > current_year:
                        # Only allow if it's "present" or "current"
                        if end_date not in ['present', 'current', 'now']:
                            print(f"[EXPERIENCE CALC] Skipping entry with future end date: {end_date} (end_year: {end_year} > current: {current_year})")
                            continue
                    # If end_year == current_year, check if end_month is more than 1 month in the future
                    elif end_year == current_year:
                        if end_month > current_month + 1:
                            # Only allow if it's "present" or "current"
                            if end_date not in ['present', 'current', 'now']:
                                print(f"[EXPERIENCE CALC] Skipping entry with future end date: {end_date} (end_month: {end_month} > current_month+1: {current_month+1})")
                                continue
                    
                    # Calculate years between dates (more accurate with months)
                    if end_year == start_year:
                        # Same year - calculate months difference
                        months_diff = end_month - start_month + 1  # +1 to include both months
                        if months_diff < 0:
                            months_diff = 12 + months_diff  # Handle wrap-around
                        entry_years = months_diff / 12.0
                    else:
                        # Different years
                        years = end_year - start_year
                        months = end_month - start_month
                        # If end month is before start month, adjust
                        if months < 0:
                            years -= 1
                            months += 12
                        # Add 1 to include both start and end months
                        total_months = years * 12 + months + 1
                        entry_years = total_months / 12.0
                    
                    total_years += entry_years
                    
                    print(f"[EXPERIENCE CALC] Entry {idx+1}: {entry_years:.2f} years ({start_date} to {end_date}), total so far: {total_years:.2f}")
                    
                except (ValueError, AttributeError, TypeError) as e:
                    print(f"[EXPERIENCE CALC] Error parsing entry {idx+1}: {e}")
                    continue
        
        # If no valid experience entries, try to extract from text patterns
        if total_years == 0.0:
            print(f"[EXPERIENCE CALC] No valid entries, trying text patterns...")
            resume_lower = resume_text.lower()
            years_patterns = [
                r'(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?experience',
                r'experience[:\s]*(\d+(?:\.\d+)?)\s*years?',
                r'(\d+(?:\.\d+)?)\+?\s*years?\s*(?:in|of)',
                r'(\d+(?:\.\d+)?)\s*yrs?\s*(?:of\s*)?experience',
            ]
            
            for pattern in years_patterns:
                match = re.search(pattern, resume_lower)
                if match:
                    try:
                        years = float(match.group(1))
                        if 0 <= years <= 50:  # Reasonable bounds
                            total_years = years
                            print(f"[EXPERIENCE CALC] Found in text: {total_years} years")
                            break
                    except (ValueError, AttributeError):
                        continue
        
        result = round(total_years, 1)
        print(f"[EXPERIENCE CALC] Final result: {result} years")
        return result
        
    except Exception as e:
        print(f"[EXPERIENCE CALC] Error calculating experience years: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

def _determine_experience_level(job_titles: List[str], resume_text: str) -> str:
    """Determine experience level from job titles and text"""
    try:
        resume_lower = resume_text.lower()
        
        # Check for years of experience
        years_patterns = [
            r'(\d+)\s*years?\s*(?:of\s*)?experience',
            r'experience[:\s]*(\d+)\s*years?',
            r'(\d+)\+?\s*years?\s*in'
        ]
        
        for pattern in years_patterns:
            match = re.search(pattern, resume_lower)
            if match:
                years = int(match.group(1))
                if years >= 5:
                    return "Senior"
                elif years >= 3:
                    return "Mid-level"
                elif years >= 1:
                    return "Junior"
        
        # Check job titles for seniority indicators
        seniority_keywords = {
            "senior": ["senior", "lead", "principal", "architect", "manager", "director"],
            "mid": ["mid-level", "intermediate", "experienced"],
            "junior": ["junior", "entry", "graduate", "intern", "trainee"]
        }
        
        all_text = " ".join(job_titles + [resume_lower])
        for level, keywords in seniority_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                return level.title()
        
        return "Unknown"
    except:
        return "Unknown"

def calculate_similarity(resume_text: str, jd_text: str) -> float:
    """Calculate semantic similarity using Sentence BERT"""
    try:
        model = _get_sbert_model()
        
        # Get embeddings
        resume_embedding = model.encode([resume_text])
        jd_embedding = model.encode([jd_text])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(resume_embedding, jd_embedding)[0][0]
        return float(similarity * 100)  # Convert to percentage
        
    except Exception as e:
        print(f"Sentence BERT error: {e}")
        return 0.0

def find_semantic_experience_header(candidate_lines: List[str], threshold: float = 0.4) -> Optional[Tuple[str, int]]:
    """
    Find experience section header using semantic similarity (cosine similarity with Sentence BERT)
    More efficient than individual comparisons - batches all candidates and keywords together
    
    Args:
        candidate_lines: List of candidate header lines to check
        threshold: Similarity threshold (0.4 = 40% similarity required)
        
    Returns:
        Tuple of (matched_line, index) if found, None otherwise
    """
    try:
        if not candidate_lines:
            return None
        
        # Experience-related keywords/phrases (semantic targets)
        # Expanded to include variations like "organizational experience", "working experience", etc.
        # NOTE: Explicitly EXCLUDING "educational experience" to avoid false positives
        experience_keywords = [
            "experience", "work experience", "professional experience", 
            "employment history", "career history", "work history",
            "professional history", "job experience", "employment",
            "internship experience", "internships", "training experience",
            "work exp", "work exp.", "professional exp", "career experience",
            "organizational experience", "working experience", "working exp",
            "prior experience", "present experience", "current experience",
            "other experience", "additional experience", "previous experience",
            "work exposure", "professional exposure", "career exposure"
        ]
        
        # Normalize candidate lines (clean and filter)
        normalized_candidates = []
        candidate_indices = []
        for i, line in enumerate(candidate_lines):
            line_clean = line.strip()
            # Filter: reasonable length, not too generic
            # Allow longer headers (up to 80 chars) for phrases like "ORGANIZATIONAL EXPERIENCE"
            if (3 <= len(line_clean) <= 80 and 
                line_clean.lower() not in ['', 'skills', 'education', 'projects', 'certifications', 'references'] and
                not line_clean.lower().startswith(('http', 'www', '@', 'email', 'phone', 'contact'))):
                normalized_candidates.append(line_clean)
                candidate_indices.append(i)
        
        if not normalized_candidates:
            print(f"[EXPERIENCE EXTRACT] No valid candidate lines found for semantic matching")
            return None
        
        print(f"[EXPERIENCE EXTRACT] Checking {len(normalized_candidates)} candidate lines for semantic match...")
        print(f"[EXPERIENCE EXTRACT] Sample candidates: {normalized_candidates[:5]}")
        
        # Batch encode all candidates and keywords together (efficient)
        model = _get_sbert_model()
        all_texts = experience_keywords + normalized_candidates
        embeddings = model.encode(all_texts)
        
        # Split embeddings: first len(experience_keywords) are keywords, rest are candidates
        keyword_embeddings = embeddings[:len(experience_keywords)]
        candidate_embeddings = embeddings[len(experience_keywords):]
        
        # Find best match: check each candidate against all keywords
        best_match = None
        best_similarity = 0.0
        
        for i, candidate_emb in enumerate(candidate_embeddings):
            # Calculate similarity against all keywords (take max)
            similarities = cosine_similarity([candidate_emb], keyword_embeddings)[0]
            max_similarity = float(np.max(similarities))
            best_keyword_idx = int(np.argmax(similarities))
            
            # Log top matches for debugging (even if below threshold)
            if max_similarity > 0.5:  # Log anything above 50% for debugging
                print(f"[EXPERIENCE EXTRACT] Candidate '{normalized_candidates[i]}' ≈ '{experience_keywords[best_keyword_idx]}' (similarity: {max_similarity:.3f})")
            
            if max_similarity >= threshold and max_similarity > best_similarity:
                best_similarity = max_similarity
                best_match = (normalized_candidates[i], candidate_indices[i], experience_keywords[best_keyword_idx], max_similarity)
        
        if best_match:
            matched_line, line_idx, matched_keyword, similarity = best_match
            print(f"[EXPERIENCE EXTRACT] [OK] Found semantic experience header: '{matched_line}' ~ '{matched_keyword}' (similarity: {similarity:.3f})")
            return (matched_line, line_idx)
        else:
            print(f"[EXPERIENCE EXTRACT] No candidate exceeded threshold {threshold} (best was below threshold)")
        
        return None
        
    except Exception as e:
        print(f"[EXPERIENCE EXTRACT] Semantic matching error: {e}")
        return None

def find_all_semantic_experience_headers(candidate_lines: List[str], resume_text: str, threshold: float = 0.4) -> List[Tuple[int, int, str]]:
    """
    Find ALL experience section headers using semantic similarity (not just the first one)
    Returns list of (start_pos, end_pos, header_name) tuples
    
    Args:
        candidate_lines: List of candidate header lines to check
        resume_text: Full resume text (to find positions)
        threshold: Similarity threshold (0.4 = 40% similarity required)
        
    Returns:
        List of (start_pos, end_pos, header_name) tuples for all matched sections
    """
    try:
        if not candidate_lines:
            return []
        
        # Experience-related keywords/phrases (same as find_semantic_experience_header)
        # Explicitly EXCLUDING "educational experience"
        experience_keywords = [
            "experience", "work experience", "professional experience", 
            "employment history", "career history", "work history",
            "professional history", "job experience", "employment",
            "internship experience", "internships", "training experience",
            "work exp", "work exp.", "professional exp", "career experience",
            "organizational experience", "working experience", "working exp",
            "prior experience", "present experience", "current experience",
            "other experience", "additional experience", "previous experience",
            "work exposure", "professional exposure", "career exposure"
        ]
        
        # Filter out educational experience explicitly
        filtered_candidates = []
        candidate_indices = []
        for i, line in enumerate(candidate_lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Skip educational experience
            if 'educational' in line_lower or 'academic experience' in line_lower:
                # Safely print line (handle Unicode characters)
                try:
                    safe_line = line_clean.encode('ascii', errors='replace').decode('ascii')
                    print(f"[EXPERIENCE EXTRACT] Skipping educational experience: '{safe_line}'")
                except Exception:
                    print(f"[EXPERIENCE EXTRACT] Skipping educational experience")
                continue
            
            # Filter: reasonable length, not too generic
            if (3 <= len(line_clean) <= 80 and 
                line_clean.lower() not in ['', 'skills', 'education', 'projects', 'certifications', 'references'] and
                not line_clean.lower().startswith(('http', 'www', '@', 'email', 'phone', 'contact'))):
                filtered_candidates.append(line_clean)
                candidate_indices.append(i)
        
        if not filtered_candidates:
            return []
        
        print(f"[EXPERIENCE EXTRACT] Checking {len(filtered_candidates)} candidate lines for semantic match...")
        
        # Batch encode all candidates and keywords together (efficient)
        model = _get_sbert_model()
        all_texts = experience_keywords + filtered_candidates
        embeddings = model.encode(all_texts)
        
        # Split embeddings: first len(experience_keywords) are keywords, rest are candidates
        keyword_embeddings = embeddings[:len(experience_keywords)]
        candidate_embeddings = embeddings[len(experience_keywords):]
        
        # Find ALL matches (not just the best one)
        matched_sections = []
        
        for i, candidate_emb in enumerate(candidate_embeddings):
            # Calculate similarity against all keywords (take max)
            similarities = cosine_similarity([candidate_emb], keyword_embeddings)[0]
            max_similarity = float(np.max(similarities))
            best_keyword_idx = int(np.argmax(similarities))
            
            if max_similarity >= threshold:
                matched_line = filtered_candidates[i]
                line_idx = candidate_indices[i]
                
                # Find the position of this line in the resume
                lines = resume_text.split('\n')
                if line_idx < len(lines):
                    target_line = lines[line_idx]
                    line_pos = resume_text.find(target_line)
                    if line_pos != -1:
                        section_start = line_pos + len(target_line)
                        
                        # Find section end (next experience section or non-experience section)
                        section_end = len(resume_text)
                        
                        # Check for next semantic experience section (simplified approach)
                        # Look for other candidates that also match
                        for j in range(i+1, len(candidate_embeddings)):
                            next_similarities = cosine_similarity([candidate_embeddings[j]], keyword_embeddings)[0]
                            next_max_sim = float(np.max(next_similarities))
                            if next_max_sim >= threshold:
                                # Found another experience section - this section ends there
                                next_line_idx = candidate_indices[j]
                                if next_line_idx < len(lines):
                                    next_target_line = lines[next_line_idx]
                                    next_line_pos = resume_text.find(next_target_line, section_start)
                                    if next_line_pos != -1 and next_line_pos < section_end:
                                        section_end = next_line_pos
                                        break
                        
                        # Check for non-experience sections
                        next_section_patterns = [
                            r'\n\s*(?:education|academic|qualification|certification|skills|projects|achievements|awards)\s*[:]?\s*\n',
                        ]
                        for next_pattern in next_section_patterns:
                            next_match = re.search(next_pattern, resume_text[section_start:], re.IGNORECASE | re.MULTILINE)
                            if next_match:
                                next_pos = section_start + next_match.start()
                                if next_pos < section_end:
                                    section_end = next_pos
                                break
                        
                        matched_sections.append((section_start, section_end, matched_line))
                        print(f"[EXPERIENCE EXTRACT] [OK] Found semantic experience header: '{matched_line}' ~ '{experience_keywords[best_keyword_idx]}' (similarity: {max_similarity:.3f})")
        
        return matched_sections
        
    except Exception as e:
        print(f"[EXPERIENCE EXTRACT] Semantic matching error (all headers): {e}")
        return []

def extract_skills_simple(resume_text: str, jd_text: str) -> tuple[List[str], List[str]]:
    """Extract common and missing skills using simple text matching"""
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()
    
    # Common technical skills
    tech_skills = [
        "python", "javascript", "java", "react", "node.js", "angular", "vue",
        "django", "flask", "express", "spring", "mongodb", "mysql", "postgresql",
        "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git", "github",
        "html", "css", "bootstrap", "tailwind", "sass", "less", "typescript",
        "php", "ruby", "go", "rust", "c++", "c#", ".net", "sql", "nosql",
        "api", "rest", "graphql", "microservices", "agile", "scrum", "devops",
        "ci/cd", "jenkins", "gitlab", "jira", "confluence", "linux", "unix"
    ]
    
    common_skills = []
    missing_skills = []
    
    for skill in tech_skills:
        if skill in resume_lower and skill in jd_lower:
            common_skills.append(skill.title())
        elif skill in jd_lower and skill not in resume_lower:
            missing_skills.append(skill.title())
    
    return common_skills, missing_skills

def generate_analysis(similarity_score: float, common_skills: List[str], missing_skills: List[str], resume_text: str) -> Dict[str, Any]:
    """Generate analysis based on similarity score and skills"""
    
    # Create deterministic seed for consistent results
    resume_hash = hashlib.md5(resume_text.encode()).hexdigest()
    timestamp = int(time.time() * 1000) % 10000
    combined_seed = int(resume_hash[:8], 16) + timestamp
    random.seed(combined_seed)
    
    # Generate reasons based on score
    reasons = []
    if similarity_score > 80:
        reasons.extend([
            "Excellent semantic match with job requirements",
            "Strong alignment with role expectations"
        ])
    elif similarity_score > 60:
        reasons.extend([
            "Good semantic similarity to job description",
            "Reasonable match with role requirements"
        ])
    else:
        reasons.extend([
            "Limited semantic alignment with job requirements",
            "May need additional relevant experience"
        ])
    
    # Add skill-based reasons
    if common_skills:
        skill_reasons = [
            f"Strong technical skills: {', '.join(common_skills[:3])}",
            f"Relevant experience with {', '.join(common_skills[:2])}"
        ]
        reasons.extend(skill_reasons[:2])
    
    # Generate strengths
    strengths = []
    if common_skills:
        strengths.extend([
            f"Technical proficiency in {', '.join(common_skills[:2])}",
            f"Strong background with {', '.join(common_skills[:3])}"
        ])
    
    # Add experience-based strengths
    experience_keywords = ["years", "experience", "senior", "lead", "manager", "director"]
    if any(keyword in resume_text.lower() for keyword in experience_keywords):
        strengths.append("Relevant professional experience")
    
    # Generate missing skills analysis
    if missing_skills:
        missing_analysis = f"Consider developing skills in: {', '.join(missing_skills[:3])}"
    else:
        missing_analysis = "All key technical skills present"
    
    # Determine overall fit
    if similarity_score > 80:
        overall_fit = "Excellent match"
    elif similarity_score > 60:
        overall_fit = "Good match"
    elif similarity_score > 40:
        overall_fit = "Fair match"
    else:
        overall_fit = "Poor match"
    
    return {
        "reasons": reasons,
        "strengths": strengths,
        "missing_skills": missing_skills,
        "overall_fit": overall_fit,
        "missing_analysis": missing_analysis
    }

async def score_resume_with_ner(resume_text: str, jd_text: str, parsed_jd: Optional[Dict[str, Any]] = None, experience_cache: Optional[Dict[str, Any]] = None, parsed_resume_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enhanced resume scoring using NER model + Sentence BERT - LEGACY VERSION (kept for compatibility)"""
    jd_lower = jd_text.lower()
    min_experience_required = _extract_jd_experience_requirement(jd_text, parsed_jd)
    return await score_resume_with_ner_optimized(
        resume_text, jd_text, jd_lower, parsed_jd, min_experience_required,
        experience_cache, parsed_resume_data
    )
    
def _extract_jd_experience_requirement(jd_text: str, parsed_jd: Optional[Dict[str, Any]] = None) -> Optional[float]:
    """Extract minimum experience requirement from JD - called once for all resumes"""
    if not jd_text:
        return None
    
    jd_lower = jd_text.lower()
    min_experience_required = None
    
    # Comprehensive experience extraction patterns
    experience_patterns = [
        # Direct patterns
        r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
        r'experience[:\s]*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?',
        r'years?\s+of\s+experience[:\s]*(\d+(?:\.\d+)?)',
        r'experience\s+level[:\s]*(\d+(?:\.\d+)?)\s*years?',
        
        # Minimum/Required patterns
        r'minimum\s+experience[:\s]*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?',
        r'minimum\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
        r'minimum\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?',
        r'required\s+experience[:\s]*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?',
        r'experience\s+required[:\s]*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?',
        r'required\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
        
        # At least patterns
        r'at\s+least\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
        r'at\s+least\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?',
        
        # Range patterns (use minimum)
        r'(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*years?\s+(?:of\s+)?experience',
        r'(\d+(?:\.\d+)?)\s*to\s*(\d+(?:\.\d+)?)\s*years?\s+(?:of\s+)?experience',
        r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)\s*years?\s+experience',
        r'experience[:\s]*(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*years?',
        
        # With context
        r'(\d+(?:\.\d+)?)\+?\s*years?\s+of\s+(?:relevant\s+)?(?:professional\s+)?experience',
        r'(\d+(?:\.\d+)?)\+?\s*yrs?\s+(?:of\s+)?experience',
        
        # Experience level mappings (convert to years)
        r'experience\s+level[:\s]*(?:senior|lead|principal|architect)',
        r'(?:senior|lead|principal|architect)\s+level\s+experience',
    ]
    
    # Removed excessive debug prints for performance
    
    for pattern in experience_patterns:
        match = re.search(pattern, jd_lower)
        if match:
            try:
                # For range patterns, use the first number (minimum)
                if len(match.groups()) >= 2:
                    min_exp = float(match.group(1))
                    max_exp = float(match.group(2)) if len(match.groups()) >= 2 else None
                    if 0 <= min_exp <= 50:
                        min_experience_required = min_exp
                        break
                elif len(match.groups()) == 1:
                    min_exp = float(match.group(1))
                    if 0 <= min_exp <= 50:
                        min_experience_required = min_exp
                        break
                else:
                    # Experience level patterns (senior, lead, etc.)
                    if 'senior' in match.group(0) or 'lead' in match.group(0) or 'principal' in match.group(0):
                        min_experience_required = 5.0  # Senior typically means 5+ years
                        break
            except (ValueError, AttributeError, IndexError):
                continue
    
    # If no pattern matched, try to extract from common sections
    if min_experience_required is None:
        # Look for experience section headers
        experience_sections = [
            r'experience\s+requirements?[:\s]*([^\n]+)',
            r'required\s+experience[:\s]*([^\n]+)',
            r'minimum\s+experience[:\s]*([^\n]+)',
            r'years?\s+of\s+experience[:\s]*([^\n]+)',
            r'experience\s+level[:\s]*([^\n]+)',
        ]
        
        for section_pattern in experience_sections:
            section_match = re.search(section_pattern, jd_lower, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1)
                # Try to extract number from section
                number_match = re.search(r'(\d+(?:\.\d+)?)', section_text)
                if number_match:
                    try:
                        min_exp = float(number_match.group(1))
                        if 0 <= min_exp <= 50:
                            min_experience_required = min_exp
                            break
                    except ValueError:
                        continue
    
    # Also check parsed JD data if available (from AI parsing)
    if min_experience_required is None and parsed_jd:
        # Check parsed JD structure for experience
        if isinstance(parsed_jd, dict):
            # Try various possible keys
            experience_keys = [
                'min_experience', 'minimum_experience', 'required_experience',
                'experience_required', 'years_of_experience', 'experience_years',
                'experience_level', 'min_years', 'required_years'
            ]
            
            for key in experience_keys:
                if key in parsed_jd:
                    value = parsed_jd[key]
                    if isinstance(value, (int, float)):
                        if 0 <= value <= 50:
                            min_experience_required = float(value)
                            break
                    elif isinstance(value, str):
                        # Try to extract number from string
                        number_match = re.search(r'(\d+(?:\.\d+)?)', str(value))
                        if number_match:
                            try:
                                min_exp = float(number_match.group(1))
                                if 0 <= min_exp <= 50:
                                    min_experience_required = min_exp
                                    break
                            except ValueError:
                                continue
            
            # Check nested structures
            if min_experience_required is None and 'requirements' in parsed_jd:
                reqs = parsed_jd['requirements']
                if isinstance(reqs, dict):
                    for req_key in ['experience', 'minimum_experience', 'years']:
                        if req_key in reqs:
                            value = reqs[req_key]
                            if isinstance(value, (int, float)):
                                if 0 <= value <= 50:
                                    min_experience_required = float(value)
                                    break
    
    return min_experience_required

async def score_resume_with_ner_optimized(
    resume_text: str, 
    jd_text: str, 
    jd_lower: str,
    parsed_jd: Optional[Dict[str, Any]] = None, 
    min_experience_required: Optional[float] = None,
    experience_cache: Optional[Dict[str, Any]] = None, 
    parsed_resume_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Optimized resume scoring - accepts pre-processed JD data to avoid redundant processing"""
    
    # OPTIMIZATION: Skip expensive extractions when cache/data available
    skip_experience = experience_cache is not None
    skip_education = True  # Education not used in scoring
    
    # Extract structured information using NER (optimized - skips unnecessary extractions)
    ner_info = extract_entities_with_ner(
        resume_text, 
        skip_experience=skip_experience,
        skip_education=skip_education,
        parsed_resume_data=parsed_resume_data
    )
    
    # Calculate similarity
    similarity_score = calculate_similarity(resume_text, jd_text)
    
    # Use NER-extracted skills instead of re-extracting
    resume_skills = ner_info.get("skills", [])
    # Extract JD skills from parsed_jd or extract from text
    if parsed_jd and isinstance(parsed_jd, dict) and "skills" in parsed_jd:
        jd_skills = parsed_jd.get("skills", [])
    else:
        # Fallback: extract from JD text
        jd_skills = _extract_skills_from_text(jd_text)
    
    # Match skills
    common_skills, missing_skills = _match_skills(resume_skills, jd_skills)
    
    # Generate analysis
    analysis = generate_analysis(similarity_score, common_skills, missing_skills, resume_text)
    
    # Use Ollama parsed years_experience directly (most accurate)
    experience_entries = []
    experience_years = 0.0
    if parsed_resume_data:
        ollama_years = parsed_resume_data.get("years_experience") or parsed_resume_data.get("experience_years")
        if ollama_years is not None:
            try:
                experience_years = float(ollama_years)
                print(f"[SCORE] Using Ollama years_experience: {experience_years}")
            except:
                pass
    if experience_years == 0.0:
        if experience_cache:
            experience_entries, experience_years = use_cached_or_extract_experience(resume_text, experience_cache)
        else:
            experience_entries = ner_info.get("experience", [])
            experience_years = _calculate_experience_years_from_entries(experience_entries, resume_text)
    
    # Use pre-extracted JD experience requirement
    if min_experience_required is None:
        min_experience_required = _extract_jd_experience_requirement(jd_text, parsed_jd)
    
    # Continue with scoring logic (same as before)
    return _calculate_final_score(
        similarity_score, common_skills, missing_skills, experience_years,
        min_experience_required, analysis, ner_info, experience_entries
    )

def _extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text using simple pattern matching"""
    text_lower = text.lower()
    tech_skills = [
        "python", "javascript", "java", "react", "node.js", "angular", "vue",
        "django", "flask", "express", "spring", "mongodb", "mysql", "postgresql",
        "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git", "github",
        "html", "css", "bootstrap", "tailwind", "sass", "less", "typescript",
        "php", "ruby", "go", "rust", "c++", "c#", ".net", "sql", "nosql",
        "api", "rest", "graphql", "microservices", "agile", "scrum", "devops",
        "ci/cd", "jenkins", "gitlab", "jira", "confluence", "linux", "unix"
    ]
    found_skills = [skill for skill in tech_skills if skill in text_lower]
    return found_skills

def _match_skills(resume_skills: List[str], jd_skills: List[str]) -> Tuple[List[str], List[str]]:
    from difflib import SequenceMatcher

    def is_match(a: str, b: str) -> bool:
        a, b = a.lower().strip(), b.lower().strip()
        if a == b:
            return True
        if a in b or b in a:
            return True
        # Abbreviation check: "ml" matches "machine learning"
        words_b = b.split()
        if len(words_b) > 1 and a == "".join(w[0] for w in words_b if w):
            return True
        words_a = a.split()
        if len(words_a) > 1 and b == "".join(w[0] for w in words_a if w):
            return True
        # Fuzzy match
        if SequenceMatcher(None, a, b).ratio() > 0.82:
            return True
        return False

    common: List[str] = []
    missing: List[str] = []

    for jd_skill in jd_skills:
        if any(is_match(jd_skill, r) for r in resume_skills):
            common.append(jd_skill)
        else:
            missing.append(jd_skill)

    return common, missing

def _calculate_final_score(
    similarity_score: float,
    common_skills: List[str],
    missing_skills: List[str],
    experience_years: float,
    min_experience_required: Optional[float],
    analysis: Dict[str, Any],
    ner_info: Dict[str, Any],
    experience_entries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate final score - extracted from score_resume_with_ner for reuse"""
    
    # Calculate skill match percentage
    total_required_skills = len(common_skills) + len(missing_skills)
    if total_required_skills > 0:
        skill_match_percentage = (len(common_skills) / total_required_skills) * 100
    else:
        skill_match_percentage = 0.0
    
    # Experience match status
    experience_match_status = "unknown"

    # If JD has no experience requirement — experience is irrelevant, give neutral score
    if min_experience_required is None or min_experience_required == 0:
        experience_bonus = 10  # neutral/slight positive
        experience_match_status = "not_required"
        if experience_years > 0:
            experience_bonus = min(20, experience_years * 2)
            experience_match_status = "bonus"
    elif experience_years == 0:
        # JD requires experience but candidate has none
        gap = min_experience_required
        if gap > 2:
            experience_bonus = 0
            experience_match_status = "poor"
        else:
            experience_bonus = 5
            experience_match_status = "fair"
    else:
        # Both JD requires and candidate has experience
        if experience_years >= min_experience_required:
            if experience_years >= min_experience_required * 1.5:
                experience_bonus = 25
                experience_match_status = "excellent"
            else:
                experience_bonus = 15
                experience_match_status = "good"
        else:
            gap = min_experience_required - experience_years
            if gap > 2:
                experience_bonus = 0
                experience_match_status = "poor"
            elif gap > 1:
                experience_bonus = 5
                experience_match_status = "fair"
            else:
                experience_bonus = 10
                experience_match_status = "fair"
    
    # Calculate weighted final score
    similarity_weight = 0.25
    skill_weight = 0.55
    experience_weight = 0.20
    
    similarity_component = similarity_score * similarity_weight
    skill_component = skill_match_percentage * skill_weight
    normalized_experience = min(100, experience_years * 10)  # Normalize to 0-100
    experience_component = normalized_experience * experience_weight
    
    final_score = similarity_component + skill_component + experience_component
    
    # Additional penalty for candidates who don't meet minimum experience
    if min_experience_required is not None and min_experience_required > 0:
        if experience_years < min_experience_required:
            gap = min_experience_required - experience_years
            if gap > 2:
                final_score = min(final_score, 70)
            elif gap > 1:
                final_score = min(final_score, 75)
    
    final_score = max(0, min(100, final_score))
    
    # Prepare detailed scores
    detailed_scores = {
        "experience_alignment": round(final_score, 1),
        "text_similarity": round(similarity_score, 1),
        "skill_match": round(skill_match_percentage, 1),
        "overall_fit_score": round(final_score, 1),
        "experience_years": round(experience_years, 1)
    }
    
    return {
        "score": int(round(final_score)),
        "overall_fit": analysis["overall_fit"],
        "experience_match": experience_match_status,
        "skill_match_percentage": round(skill_match_percentage, 1),
        "reasons": analysis["reasons"],
        "strengths": analysis["strengths"],
        "missing_skills": analysis["missing_skills"],
        "detailed_scores": detailed_scores,
        "candidate_name": ner_info["candidate_name"],
        "email": ner_info["email"],
        "phone": ner_info["phone"],
        "location": ner_info["location"],
        "extracted_skills": ner_info["skills"],
        "experience_level": ner_info["experience_level"],
        "companies": ner_info["companies"],
        "job_titles": ner_info["job_titles"],
        "education": ner_info["education"]
    }

    
    # Calculate experience bonus and alignment based on:
    # 1. Meeting/exceeding JD requirements (if specified)
    # 2. Absolute years of experience (more is generally better)
    experience_bonus = 0.0
    experience_match_status = "unknown"  # Will be set to "good", "fair", or "poor"
    
    # Determine experience match status FIRST (before calculating bonus)
    if min_experience_required is not None and min_experience_required > 0:
        # JD has experience requirement - check if candidate meets it
        if experience_years >= min_experience_required:
            # Meets or exceeds requirement
            if experience_years >= min_experience_required * 1.5:
                experience_match_status = "excellent"
            else:
                experience_match_status = "good"
            print(f"[SCORE] Experience meets requirement: {experience_years:.1f} >= {min_experience_required:.1f} years")
        else:
            # Below requirement - determine severity
            gap = min_experience_required - experience_years
            if gap <= 1:
                experience_match_status = "fair"  # Close but not quite
            elif gap <= 2:
                experience_match_status = "poor"  # Significantly below
            else:
                experience_match_status = "poor"  # Far below requirement
            print(f"[SCORE] Experience below requirement: {experience_years:.1f} < {min_experience_required:.1f} years (gap: {gap:.1f})")
    else:
        # No JD requirement specified - use experience level as indicator
        if experience_years >= 5:
            experience_match_status = "good"
        elif experience_years >= 2:
            experience_match_status = "fair"
        elif experience_years > 0:
            experience_match_status = "fair"
        else:
            experience_match_status = "poor"  # No experience at all
        print(f"[SCORE] No JD requirement, using experience level: {experience_years:.1f} years -> {experience_match_status}")
    
    # Calculate experience bonus based on match status
    if experience_years > 0:
        # Base bonus: 2 points per year of experience (capped at 15 points for 7.5+ years)
        experience_bonus = min(15, experience_years * 2)
        
        # Additional bonus for meeting/exceeding requirements
        if min_experience_required is not None:
            if experience_years >= min_experience_required:
                # Meets or exceeds requirement: additional 10 points
                requirement_bonus = 10
                # If significantly exceeds (50%+ more), extra 5 points
                if experience_years >= min_experience_required * 1.5:
                    requirement_bonus = 15
                experience_bonus += requirement_bonus
                print(f"[SCORE] Experience meets requirement: +{requirement_bonus} bonus")
            else:
                # Below requirement: STRONG penalty based on gap
                gap = min_experience_required - experience_years
                if gap <= 1:
                    # Close to requirement: moderate penalty (-10)
                    experience_bonus -= 10
                elif gap <= 2:
                    # Significantly below: large penalty (-20)
                    experience_bonus -= 20
                else:
                    # Far below: very large penalty (-30)
                    experience_bonus -= 30
                experience_bonus = max(0, experience_bonus)  # Don't go negative
                print(f"[SCORE] Experience below requirement by {gap:.1f} years: penalty -{abs(experience_bonus - min(15, experience_years * 2))} applied")
        else:
            # No JD requirement specified, but still give bonus for having experience
            print(f"[SCORE] No JD requirement, giving base experience bonus")
    else:
        # Zero experience - apply penalty if JD has requirement
        if min_experience_required is not None and min_experience_required > 0:
            # Heavy penalty for zero experience when JD requires experience
            experience_bonus = -30  # Strong negative penalty
            print(f"[SCORE] Zero experience with JD requirement of {min_experience_required:.1f} years: heavy penalty applied")
        else:
            # No JD requirement, no experience - neutral
            experience_bonus = 0
            print(f"[SCORE] Zero experience, no JD requirement: neutral")
    
    # Calculate skill match percentage FIRST (needed for final score calculation)
    total_required_skills = len(common_skills) + len(missing_skills)
    if total_required_skills == 0:
        skill_match_percentage = 0.0
    elif len(common_skills) == 0:
        skill_match_percentage = 0.0
    else:
        skill_match_percentage = (len(common_skills) / total_required_skills) * 100
        skill_match_percentage = min(100.0, max(0.0, skill_match_percentage))
    
    # Calculate skill bonus based on PERCENTAGE match, not just count
    # This ensures missing skills properly reduce the score
    # Formula: skill_match_percentage * 0.30 (30% weight for skills in final score)
    skill_bonus = skill_match_percentage * 0.30
    
    # Calculate final score using weighted components
    # Weighted: 25% similarity, 55% skills (based on match %), 20% experience
    similarity_weight = 0.25
    skill_weight = 0.55
    experience_weight = 0.20
    
    # Normalize experience bonus to 0-100 scale for weighted calculation
    # Experience bonus can be negative, so we need to handle that
    # Shift experience_bonus to 0-100 range: (bonus + 30) / 60 * 100
    # This maps: -30 (worst) -> 0, 0 (neutral) -> 50, 30 (best) -> 100
    normalized_experience = max(0, min(100, (experience_bonus + 30) / 60 * 100))
    
    # Calculate weighted final score
    similarity_component = similarity_score * similarity_weight
    skill_component = skill_match_percentage * skill_weight
    experience_component = normalized_experience * experience_weight
    
    final_score = similarity_component + skill_component + experience_component
    
    print(f"[SCORE] Weighted components: similarity={similarity_component:.1f} (50%), skills={skill_component:.1f} (30%), experience={experience_component:.1f} (20%)")
    
    # Additional penalty for candidates who don't meet minimum experience
    # This ensures they don't rank at the top even with high skills
    if min_experience_required is not None and min_experience_required > 0:
        if experience_years < min_experience_required:
            gap = min_experience_required - experience_years
            if gap > 2:
                # Far below requirement: cap score at 70 to prevent top ranking
                final_score = min(final_score, 70)
                print(f"[SCORE] Candidate far below requirement ({gap:.1f} years), capping score at 70")
            elif gap > 1:
                # Moderately below: cap at 75
                final_score = min(final_score, 75)
                print(f"[SCORE] Candidate below requirement ({gap:.1f} years), capping score at 75")
    
    final_score = max(0, min(100, final_score))  # Cap between 0 and 100
    
    print(f"[SCORE] Raw components: similarity={similarity_score:.1f}%, skill_match={skill_match_percentage:.1f}%, experience_bonus={experience_bonus:.1f}")
    print(f"[SCORE] Final weighted score: {final_score:.1f}%")
    print(f"[SCORE] Breakdown: {similarity_component:.1f} (similarity) + {skill_component:.1f} (skills) + {experience_component:.1f} (experience)")
    print(f"[SCORE] Common skills: {len(common_skills)}, Missing skills: {len(missing_skills)}, Total required: {total_required_skills}")
    
    # Prepare detailed scores for frontend
    detailed_scores = {
        "experience_alignment": round(final_score, 1),
        "text_similarity": round(similarity_score, 1),
        "skill_match": round(skill_match_percentage, 1),
        "overall_fit_score": round(final_score, 1),
        "experience_years": round(experience_years, 1)  # Add experience in years
    }
    
    return {
        "score": int(round(final_score)),
        "overall_fit": analysis["overall_fit"],
        "experience_match": experience_match_status,  # Use calculated experience match status
        "skill_match_percentage": round(skill_match_percentage, 1),
        "reasons": analysis["reasons"],
        "strengths": analysis["strengths"],
        "missing_skills": analysis["missing_skills"],
        "detailed_scores": detailed_scores,
        # Add NER extracted information
        "candidate_name": ner_info["candidate_name"],
        "email": ner_info["email"],
        "phone": ner_info["phone"],
        "location": ner_info["location"],
        "extracted_skills": ner_info["skills"],
        "experience_level": ner_info["experience_level"],
        "companies": ner_info["companies"],
        "job_titles": ner_info["job_titles"],
        "education": ner_info["education"]
    }

async def score_multiple_resumes_with_ner(resume_jd_pairs: List[tuple]) -> List[Dict[str, Any]]:
    """Score multiple resumes using NER model + Sentence BERT - OPTIMIZED FOR PARALLEL PROCESSING
    
    Args:
        resume_jd_pairs: List of tuples. Can be:
            - (resume_text, jd_text)
            - (resume_text, jd_text, parsed_jd)
            - (resume_text, jd_text, parsed_jd, experience_cache)
            - (resume_text, jd_text, parsed_jd, experience_cache, parsed_resume_data)
    """
    
    if not resume_jd_pairs:
        return []
    
    # Extract JD data once (same for all resumes)
    first_pair = resume_jd_pairs[0]
    if len(first_pair) >= 2:
        jd_text = first_pair[1]
        parsed_jd = first_pair[2] if len(first_pair) >= 3 else None
        # Preprocess JD once
        jd_lower = jd_text.lower()
        # Extract JD experience requirements once
        min_experience_required = _extract_jd_experience_requirement(jd_text, parsed_jd)
    else:
        jd_text = ""
        parsed_jd = None
        jd_lower = ""
        min_experience_required = None
    
    print(f"Processing {len(resume_jd_pairs)} resumes in parallel...")
    start_time = time.time()
    
    # Process all resumes in parallel using asyncio.gather
    async def process_single_resume(pair, index):
        try:
            # Handle tuples of different lengths
            if len(pair) == 5:
                resume_text, _, _, experience_cache, parsed_resume_data = pair
            elif len(pair) == 4:
                resume_text, _, _, experience_cache = pair
                parsed_resume_data = None
            elif len(pair) == 3:
                resume_text, _, _ = pair
                experience_cache = None
                parsed_resume_data = None
            else:
                resume_text, _ = pair
                experience_cache = None
                parsed_resume_data = None
            
            # Use pre-processed JD data
            result = await score_resume_with_ner_optimized(
                resume_text, jd_text, jd_lower, parsed_jd, min_experience_required, 
                experience_cache, parsed_resume_data
            )
            return result
        except Exception as e:
            import traceback
            print(f"[ERROR] Error processing resume {index}: {e}")
            # Return fallback result
            return {
                "score": 50,
                "overall_fit": "Fair match",
                "experience_match": "fair",
                "skill_match_percentage": 0,
                "reasons": ["Processing error - using fallback"],
                "strengths": ["Fallback processing"],
                "missing_skills": [],
                "detailed_scores": {
                    "experience_alignment": 50,
                    "text_similarity": 50,
                    "skill_match": 0,
                    "overall_fit_score": 50
                },
                "candidate_name": "Unknown",
                "email": "",
                "phone": "",
                "location": "",
                "extracted_skills": [],
                "experience_level": "Unknown",
                "companies": [],
                "job_titles": [],
                "education": []
            }
    
    # Process all resumes in parallel
    tasks = [process_single_resume(pair, i) for i, pair in enumerate(resume_jd_pairs)]
    results = await asyncio.gather(*tasks)
    
    elapsed_time = time.time() - start_time
    print(f"Processing completed in {elapsed_time:.2f} seconds ({len(results)} resumes)")
    
    return results

def build_experience_cache(resume_text: str) -> Dict[str, Any]:
    """Build a reusable cache for experience extraction to be stored with the resume.
    Returns a dict with entries, total_years, version, and created_at.
    """
    entries = extract_experience_with_spacy(resume_text)
    total_years = _calculate_experience_years_from_entries(entries, resume_text)
    return {
        "version": EXPERIENCE_EXTRACTION_VERSION,
        "entries": entries,
        "total_years": total_years,
        "created_at": int(time.time())
    }

def use_cached_or_extract_experience(resume_text: str, cached: Optional[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
    """Return (entries, total_years) using cache when valid, else extract and build cache.
    A cache is valid when its version matches EXPERIENCE_EXTRACTION_VERSION and it has entries or total_years computed.
    OPTIMIZED: If cache is valid, resume_text is not used at all.
    """
    try:
        if cached and isinstance(cached, dict):
            if cached.get("version") == EXPERIENCE_EXTRACTION_VERSION:
                cached_entries = cached.get("entries") or []
                cached_years = cached.get("total_years")
                if cached_entries or (isinstance(cached_years, (int, float)) and cached_years >= 0):
                    # Cache is valid - return immediately without processing resume_text
                    return cached_entries, float(cached_years or 0.0)
        # Fallback: extract now (only if cache invalid/missing)
        fresh = build_experience_cache(resume_text)
        return fresh["entries"], float(fresh["total_years"])  # caller may persist fresh if desired
    except Exception:
        # Hard fallback to on-the-fly extraction to avoid breaking flows
        entries = extract_experience_with_spacy(resume_text)
        years = _calculate_experience_years_from_entries(entries, resume_text)
        return entries, years
