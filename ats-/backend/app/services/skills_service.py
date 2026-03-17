"""
Skills Service for managing comprehensive skills, job profiles, and certifications.

This service provides a centralized interface for all skill-related operations
including skill matching, job profile suggestions, and certification tracking.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from app.services.resume_matching.comprehensive_skills import (
    COMPREHENSIVE_SKILLS, 
    ADDITIONAL_SKILLS, 
    JOB_PROFILES, 
    CERTIFICATIONS,
    get_all_skills,
    get_skills_by_category,
    get_all_job_profiles,
    get_all_certifications,
    search_skills
)

logger = logging.getLogger(__name__)


class SkillsService:
    """
    Centralized service for managing skills, job profiles, and certifications.
    """
    
    def __init__(self):
        """Initialize the skills service."""
        self.all_skills = get_all_skills()
        self.job_profiles = get_all_job_profiles()
        self.certifications = get_all_certifications()
        self.combined_skills = {**COMPREHENSIVE_SKILLS, **ADDITIONAL_SKILLS}
        
        logger.info("Initialized SkillsService with comprehensive skills database")
    
    def get_skill_categories(self) -> List[str]:
        """Get all available skill categories."""
        return list(self.combined_skills.keys())
    
    def get_skills_by_category(self, category: str) -> List[str]:
        """Get skills for a specific category."""
        return self.combined_skills.get(category, [])
    
    def search_skills(self, query: str, limit: int = 10) -> List[str]:
        """
        Search for skills that match the given query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching skills
        """
        query_lower = query.lower()
        matching_skills = []
        
        for category, skills in self.combined_skills.items():
            for skill in skills:
                if query_lower in skill.lower():
                    matching_skills.append(skill)
                    if len(matching_skills) >= limit:
                        return matching_skills
        
        return list(set(matching_skills))[:limit]
    
    def extract_skills_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills from text and categorize them.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            Dictionary with category as key and list of found skills as value
        """
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in self.combined_skills.items():
            category_skills = []
            for skill in skills:
                if skill.lower() in text_lower:
                    category_skills.append(skill)
            
            if category_skills:
                found_skills[category] = category_skills
        
        return found_skills
    
    def get_skill_match_score(self, resume_skills: List[str], jd_skills: List[str]) -> Dict[str, float]:
        """
        Calculate skill match score between resume and job description.
        
        Args:
            resume_skills: List of skills from resume
            jd_skills: List of skills from job description
            
        Returns:
            Dictionary with match metrics
        """
        resume_set = set(skill.lower() for skill in resume_skills)
        jd_set = set(skill.lower() for skill in jd_skills)
        
        # Calculate matches
        matches = resume_set.intersection(jd_set)
        total_jd_skills = len(jd_set)
        total_resume_skills = len(resume_set)
        
        # Calculate scores
        match_percentage = (len(matches) / total_jd_skills * 100) if total_jd_skills > 0 else 0
        coverage_percentage = (len(matches) / total_resume_skills * 100) if total_resume_skills > 0 else 0
        
        return {
            "matched_skills": list(matches),
            "match_count": len(matches),
            "total_jd_skills": total_jd_skills,
            "total_resume_skills": total_resume_skills,
            "match_percentage": round(match_percentage, 2),
            "coverage_percentage": round(coverage_percentage, 2),
            "missing_skills": list(jd_set - resume_set),
            "extra_skills": list(resume_set - jd_set)
        }
    
    def suggest_job_profiles(self, skills: List[str], limit: int = 5) -> List[Dict[str, any]]:
        """
        Suggest job profiles based on skills.
        
        Args:
            skills: List of skills
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested job profiles with match scores
        """
        skill_set = set(skill.lower() for skill in skills)
        suggestions = []
        
        for category, profiles in self.job_profiles.items():
            # Calculate how many skills match this category
            category_skills = self.combined_skills.get(category.lower().replace(" ", "_").replace("&", ""), [])
            category_skill_set = set(skill.lower() for skill in category_skills)
            
            matches = skill_set.intersection(category_skill_set)
            if matches:
                match_score = len(matches) / len(category_skill_set) * 100
                suggestions.append({
                    "category": category,
                    "profiles": profiles,
                    "match_score": round(match_score, 2),
                    "matched_skills": list(matches)
                })
        
        # Sort by match score and return top suggestions
        suggestions.sort(key=lambda x: x["match_score"], reverse=True)
        return suggestions[:limit]
    
    def get_certifications_by_category(self, category: str) -> List[str]:
        """Get certifications for a specific category."""
        return self.certifications.get(category, [])
    
    def get_certification_categories(self) -> List[str]:
        """Get all available certification categories."""
        return list(self.certifications.keys())
    
    def suggest_certifications(self, skills: List[str], limit: int = 5) -> List[Dict[str, any]]:
        """
        Suggest certifications based on skills.
        
        Args:
            skills: List of skills
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested certifications with relevance scores
        """
        skill_set = set(skill.lower() for skill in skills)
        suggestions = []
        
        for category, certs in self.certifications.items():
            # Map certification categories to skill categories
            category_mapping = {
                "cloud_certifications": ["engineering_software_qa", "it_information_security"],
                "data_certifications": ["data_science_analytics", "engineering_software_qa"],
                "cybersecurity_certifications": ["it_information_security", "engineering_software_qa"],
                "networking_certifications": ["engineering_hardware_networks", "it_information_security"],
                "devops_certifications": ["engineering_software_qa", "project_program_management"],
                "software_engineering_certifications": ["engineering_software_qa"],
                "project_management_certifications": ["project_program_management", "consulting"],
                "ai_ml_certifications": ["data_science_analytics", "engineering_software_qa"],
                "database_certifications": ["engineering_software_qa", "data_science_analytics"],
                "it_service_management_certifications": ["it_information_security", "project_program_management"]
            }
            
            relevant_categories = category_mapping.get(category, [])
            total_relevance = 0
            
            for skill_category in relevant_categories:
                category_skills = self.combined_skills.get(skill_category, [])
                category_skill_set = set(skill.lower() for skill in category_skills)
                matches = skill_set.intersection(category_skill_set)
                if matches:
                    total_relevance += len(matches) / len(category_skill_set) * 100
            
            if total_relevance > 0:
                suggestions.append({
                    "category": category,
                    "certifications": certs,
                    "relevance_score": round(total_relevance / len(relevant_categories), 2)
                })
        
        # Sort by relevance score and return top suggestions
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
        return suggestions[:limit]
    
    def get_skill_statistics(self) -> Dict[str, int]:
        """Get statistics about the skills database."""
        total_skills = sum(len(skills) for skills in self.combined_skills.values())
        total_job_profiles = sum(len(profiles) for profiles in self.job_profiles.values())
        total_certifications = sum(len(certs) for certs in self.certifications.values())
        
        return {
            "total_skill_categories": len(self.combined_skills),
            "total_skills": total_skills,
            "total_job_profile_categories": len(self.job_profiles),
            "total_job_profiles": total_job_profiles,
            "total_certification_categories": len(self.certifications),
            "total_certifications": total_certifications
        }
    
    def normalize_skill(self, skill: str) -> Optional[str]:
        """
        Normalize a skill name using the skills database.
        
        Args:
            skill: Skill name to normalize
            
        Returns:
            Normalized skill name or None if not found
        """
        return self.all_skills.get(skill.lower())
    
    def get_related_skills(self, skill: str, limit: int = 5) -> List[str]:
        """
        Get skills related to the given skill.
        
        Args:
            skill: Skill to find related skills for
            limit: Maximum number of related skills
            
        Returns:
            List of related skills
        """
        related_skills = []
        skill_lower = skill.lower()
        
        # Find the category of the given skill
        skill_category = None
        for category, skills in self.combined_skills.items():
            if any(skill_lower == s.lower() for s in skills):
                skill_category = category
                break
        
        if skill_category:
            # Get other skills from the same category
            category_skills = self.combined_skills[skill_category]
            for s in category_skills:
                if s.lower() != skill_lower:
                    related_skills.append(s)
                    if len(related_skills) >= limit:
                        break
        
        return related_skills


# Global instance
skills_service = SkillsService()
