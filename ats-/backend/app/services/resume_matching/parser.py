"""
Resume Parser Module
Extracts structured data from PDF and DOCX resume files using NLP and regex.
"""

import re
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

import pdfplumber
from docx import Document
import spacy
from spacy.matcher import Matcher

from .models import ResumeData, FileType, ProcessingStatus
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Advanced resume parser using NLP and regex patterns.
    Handles both PDF and DOCX files with high accuracy extraction.
    """
    
    def __init__(self):
        """Initialize the parser with NLP model and patterns."""
        try:
            # Load spaCy model (download with: python -m spacy download en_core_web_sm)
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        self._setup_patterns()
        
        # Regex patterns for extraction
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        self.phone_pattern = re.compile(
            r'(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}'
        )
        
        self.experience_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience', re.IGNORECASE),
            re.compile(r'experience\s*:?\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?', re.IGNORECASE),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*yrs?\s+(?:of\s+)?(?:experience|exp)', re.IGNORECASE),
        ]
        
        # Common skills database for normalization
        self.skills_database = self._load_skills_database()
    
    def _setup_patterns(self) -> None:
        """Setup spaCy patterns for named entity recognition."""
        if not self.matcher:
            return
        
        # Pattern for years of experience
        experience_pattern = [
            {"LIKE_NUM": True},
            {"LOWER": {"IN": ["years", "year", "yrs", "yr"]}},
            {"LOWER": {"IN": ["of", ""]}, "OP": "?"},
            {"LOWER": "experience"}
        ]
        self.matcher.add("EXPERIENCE", [experience_pattern])
    
    def _load_skills_database(self) -> Dict[str, str]:
        """Load and return normalized skills mapping."""
        # This would typically be loaded from a file or database
        return {
            # Programming languages
            "python3": "Python",
            "python 3": "Python",
            "py": "Python",
            "javascript": "JavaScript",
            "js": "JavaScript",
            "typescript": "TypeScript",
            "ts": "TypeScript",
            "java": "Java",
            "c++": "C++",
            "cpp": "C++",
            "csharp": "C#",
            "c#": "C#",
            
            # Frameworks
            "reactjs": "React",
            "react.js": "React",
            "vuejs": "Vue.js",
            "vue.js": "Vue.js",
            "angular": "Angular",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "django": "Django",
            "flask": "Flask",
            "fastapi": "FastAPI",
            "express": "Express.js",
            "expressjs": "Express.js",
            
            # Databases
            "mysql": "MySQL",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mongodb": "MongoDB",
            "mongo": "MongoDB",
            "redis": "Redis",
            "sqlite": "SQLite",
            
            # Cloud & DevOps
            "aws": "AWS",
            "amazon web services": "AWS",
            "azure": "Azure",
            "gcp": "Google Cloud",
            "google cloud": "Google Cloud",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "jenkins": "Jenkins",
            
            # Data Science
            "machine learning": "Machine Learning",
            "ml": "Machine Learning",
            "artificial intelligence": "AI",
            "ai": "AI",
            "deep learning": "Deep Learning",
            "dl": "Deep Learning",
            "pandas": "Pandas",
            "numpy": "NumPy",
            "scikit-learn": "Scikit-learn",
            "sklearn": "Scikit-learn",
            "tensorflow": "TensorFlow",
            "pytorch": "PyTorch",
        }
    
    def extract_text_from_pdf(self, file_path: Union[str, Path]) -> str:
        """Extract text from PDF file using pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: Union[str, Path]) -> str:
        """Extract text from DOCX file using python-docx."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            return ""
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume text."""
        if not self.nlp:
            return None
        
        doc = self.nlp(text[:1000])  # Process first 1000 characters
        
        # Look for PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Filter out common false positives
                name = ent.text.strip()
                if len(name.split()) >= 2 and not any(word.lower() in [
                    "resume", "cv", "curriculum", "vitae", "profile", "summary"
                ] for word in name.split()):
                    return name
        
        # Fallback: Look for name patterns in first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if len(line.split()) == 2 and line.replace(' ', '').isalpha():
                return line
        
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume text."""
        matches = self.email_pattern.findall(text)
        if matches:
            # Return the first valid email found
            return matches[0].lower()
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume text."""
        matches = self.phone_pattern.findall(text)
        if matches:
            # Clean and format the phone number
            phone = re.sub(r'[^\d+]', '', matches[0])
            return phone
        return None
    
    def extract_experience(self, text: str) -> Optional[float]:
        """Extract years of experience from resume text."""
        # Try regex patterns
        for pattern in self.experience_patterns:
            matches = pattern.findall(text)
            if matches:
                try:
                    years = float(matches[0])
                    if 0 <= years <= 50:  # Reasonable bounds
                        return years
                except ValueError:
                    continue
        
        # Try spaCy matcher if available
        if self.nlp and self.matcher:
            doc = self.nlp(text)
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                # Extract number from the span
                for token in span:
                    if token.like_num:
                        try:
                            years = float(token.text)
                            if 0 <= years <= 50:
                                return years
                        except ValueError:
                            continue
        
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract and normalize skills from resume text."""
        skills = set()
        text_lower = text.lower()
        
        # Extract skills from our database
        for skill_variant, normalized_skill in self.skills_database.items():
            if skill_variant in text_lower:
                skills.add(normalized_skill)
        
        # Additional skill extraction using NLP if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract technology-related entities
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"] and len(ent.text) > 2:
                    # Check if it's a known technology
                    normalized = self.skills_database.get(ent.text.lower())
                    if normalized:
                        skills.add(normalized)
        
        return list(skills)
    
    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize skill names using the skills database."""
        normalized = []
        for skill in skills:
            normalized_skill = self.skills_database.get(skill.lower(), skill)
            if normalized_skill not in normalized:
                normalized.append(normalized_skill)
        return normalized
    
    def parse_resume(self, file_path: Union[str, Path]) -> ResumeData:
        """
        Parse a single resume file and extract structured data.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            ResumeData object with extracted information
        """
        file_path = Path(file_path)
        
        # Determine file type
        file_extension = file_path.suffix.lower()
        if file_extension == '.pdf':
            file_type = FileType.PDF
            text = self.extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            file_type = FileType.DOCX
            text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return ResumeData(
                file_name=file_path.name,
                file_type=file_type,
                raw_text="",
                processing_status=ProcessingStatus.FAILED
            )
        
        try:
            # Extract structured data
            name = self.extract_name(text)
            email = self.extract_email(text)
            phone = self.extract_phone(text)
            experience = self.extract_experience(text)
            skills = self.extract_skills(text)
            skills = self.normalize_skills(skills)
            
            resume_data = ResumeData(
                file_name=file_path.name,
                file_type=file_type,
                name=name,
                email=email,
                phone=phone,
                years_of_experience=experience,
                skills=skills,
                raw_text=text,
                processing_status=ProcessingStatus.COMPLETED
            )
            
            logger.info(f"Successfully parsed {file_path.name}")
            return resume_data
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return ResumeData(
                file_name=file_path.name,
                file_type=file_type,
                raw_text=text,
                processing_status=ProcessingStatus.FAILED
            )


def parse_resume_worker(file_path: str) -> ResumeData:
    """Worker function for multiprocessing resume parsing."""
    parser = ResumeParser()
    return parser.parse_resume(file_path)


class BulkResumeParser:
    """
    Bulk resume parser for processing large numbers of resumes efficiently.
    Uses multiprocessing for scalability up to 1M+ resumes.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize bulk parser.
        
        Args:
            max_workers: Maximum number of worker processes
        """
        self.max_workers = max_workers or min(mp.cpu_count(), settings.max_workers)
        logger.info(f"Initialized BulkResumeParser with {self.max_workers} workers")
    
    def parse_resumes(self, file_paths: List[Union[str, Path]]) -> List[ResumeData]:
        """
        Parse multiple resume files in parallel.
        
        Args:
            file_paths: List of paths to resume files
            
        Returns:
            List of ResumeData objects
        """
        if not file_paths:
            return []
        
        logger.info(f"Starting bulk parsing of {len(file_paths)} resumes")
        
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_path = {
                executor.submit(parse_resume_worker, str(path)): path 
                for path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if len(results) % 100 == 0:
                        logger.info(f"Processed {len(results)}/{len(file_paths)} resumes")
                        
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    # Create failed result
                    results.append(ResumeData(
                        file_name=Path(path).name,
                        file_type=FileType.PDF,  # Default
                        raw_text="",
                        processing_status=ProcessingStatus.FAILED
                    ))
        
        logger.info(f"Completed bulk parsing. {len(results)} resumes processed")
        return results
    
    async def parse_resumes_async(self, file_paths: List[Union[str, Path]]) -> List[ResumeData]:
        """
        Asynchronous version of bulk resume parsing.
        
        Args:
            file_paths: List of paths to resume files
            
        Returns:
            List of ResumeData objects
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parse_resumes, file_paths)


# Convenience functions
def parse_single_resume(file_path: Union[str, Path]) -> ResumeData:
    """Parse a single resume file."""
    parser = ResumeParser()
    return parser.parse_resume(file_path)


def parse_bulk_resumes(
    file_paths: List[Union[str, Path]], 
    max_workers: Optional[int] = None
) -> List[ResumeData]:
    """Parse multiple resume files in parallel."""
    parser = BulkResumeParser(max_workers)
    return parser.parse_resumes(file_paths)
