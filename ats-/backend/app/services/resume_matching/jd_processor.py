"""
Job Description Processor Module
Extracts required skills and processes job descriptions for matching.
"""

import re
import logging
from typing import List, Optional, Dict, Set
import spacy
from spacy.matcher import Matcher

from .models import JobDescription
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JDProcessor:
    """
    Job Description processor for extracting structured information.
    Uses NLP and regex patterns to identify skills and requirements.
    """
    
    def __init__(self):
        """Initialize the JD processor with NLP models and patterns."""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        self._setup_patterns()
        
        # Experience patterns
        self.experience_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience', re.IGNORECASE),
            re.compile(r'experience\s*:?\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?', re.IGNORECASE),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*yrs?\s+(?:of\s+)?(?:experience|exp)', re.IGNORECASE),
            re.compile(r'minimum\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?', re.IGNORECASE),
            re.compile(r'at\s+least\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?', re.IGNORECASE),
        ]
        
        # Range patterns (e.g., "3-5 years")
        self.experience_range_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*years?', re.IGNORECASE),
            re.compile(r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)\s*years?', re.IGNORECASE),
        ]
        
        # Skills database for extraction
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
        from .comprehensive_skills import get_all_skills
        return get_all_skills()
    
    def extract_experience_requirements(self, text: str) -> tuple[Optional[float], Optional[float]]:
        """
        Extract minimum and maximum experience requirements from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Tuple of (min_experience, max_experience)
        """
        min_exp = None
        max_exp = None
        
        # Try range patterns first
        for pattern in self.experience_range_patterns:
            matches = pattern.findall(text)
            if matches:
                try:
                    min_val, max_val = matches[0]
                    min_exp = float(min_val)
                    max_exp = float(max_val)
                    break
                except (ValueError, IndexError):
                    continue
        
        # If no range found, try single value patterns
        if min_exp is None:
            for pattern in self.experience_patterns:
                matches = pattern.findall(text)
                if matches:
                    try:
                        years = float(matches[0])
                        if 0 <= years <= 50:  # Reasonable bounds
                            min_exp = years
                            break
                    except ValueError:
                        continue
        
        return min_exp, max_exp
    
    def extract_skills(self, text: str) -> tuple[List[str], List[str]]:
        """
        Extract required and preferred skills from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Tuple of (required_skills, preferred_skills)
        """
        text_lower = text.lower()
        required_skills = set()
        preferred_skills = set()
        
        # Look for skills sections
        skills_sections = [
            "required skills", "must have", "essential skills", "core skills",
            "technical requirements", "required qualifications", "must know"
        ]
        
        preferred_sections = [
            "preferred skills", "nice to have", "bonus skills", "additional skills",
            "would be great", "advantageous", "plus"
        ]
        
        # Extract skills from required sections
        for section in skills_sections:
            if section in text_lower:
                # Find the section and extract skills from it
                section_start = text_lower.find(section)
                if section_start != -1:
                    # Get text after the section header
                    section_text = text[section_start:section_start + 1000]
                    required_skills.update(self._extract_skills_from_text(section_text))
        
        # Extract skills from preferred sections
        for section in preferred_sections:
            if section in text_lower:
                section_start = text_lower.find(section)
                if section_start != -1:
                    section_text = text[section_start:section_start + 1000]
                    preferred_skills.update(self._extract_skills_from_text(section_text))
        
        # If no specific sections found, extract all skills and mark as required
        if not required_skills and not preferred_skills:
            all_skills = self._extract_skills_from_text(text)
            required_skills = all_skills
        
        return list(required_skills), list(preferred_skills)
    
    def _extract_skills_from_text(self, text: str) -> Set[str]:
        """Extract skills from a given text using the skills database."""
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
        
        return skills
    
    def extract_job_title(self, text: str) -> Optional[str]:
        """Extract job title from job description."""
        if not self.nlp:
            return None
        
        doc = self.nlp(text[:500])  # Process first 500 characters
        
        # Look for job title patterns
        title_patterns = [
            r'(senior|lead|principal|junior)?\s*(software|web|frontend|backend|full[\s-]?stack|ui/ux|react|angular|vue)?\s*(engineer|developer|programmer|designer|architect|analyst|consultant|manager|intern|specialist)',
            r'(technical|project|product|engineering|development)\s+(manager|lead|director)',
            r'(ui|ux|product|graphic|web)\s+designer',
            r'(data|business|systems?)\s+analyst',
            r'(devops|qa|test|quality\s+assurance)\s+(engineer|analyst|specialist)'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from job description."""
        if not self.nlp:
            return None
        
        doc = self.nlp(text[:1000])  # Process first 1000 characters
        
        # Look for ORG entities that might be company names
        for ent in doc.ents:
            if ent.label_ == "ORG" and len(ent.text) > 2:
                # Filter out common false positives
                if not any(word in ent.text.lower() for word in [
                    "company", "corporation", "inc", "llc", "ltd", "limited"
                ]):
                    return ent.text
        
        return None
    
    def process_job_description(
        self, 
        description_text: str, 
        title: str = None, 
        company: str = None
    ) -> JobDescription:
        """
        Process a job description and extract structured information.
        
        Args:
            description_text: Raw job description text
            title: Optional job title
            company: Optional company name
            
        Returns:
            Processed JobDescription object
        """
        # Extract information
        extracted_title = title or self.extract_job_title(description_text)
        extracted_company = company or self.extract_company_name(description_text)
        min_exp, max_exp = self.extract_experience_requirements(description_text)
        required_skills, preferred_skills = self.extract_skills(description_text)
        
        # Create JobDescription object
        jd = JobDescription(
            title=extracted_title or "Unknown Position",
            company=extracted_company,
            description=description_text,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_experience=min_exp,
            max_experience=max_exp
        )
        
        logger.info(f"Processed JD: {jd.title} at {jd.company or 'Unknown'}")
        logger.info(f"Required skills: {len(required_skills)}, Preferred skills: {len(preferred_skills)}")
        
        return jd


# Convenience function
def process_job_description(description_text: str, title: str = None, company: str = None) -> JobDescription:
    """Process a job description and return structured data."""
    processor = JDProcessor()
    return processor.process_job_description(description_text, title, company)
