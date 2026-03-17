"""
Resume Matcher Module
Handles matching resumes against job descriptions using vector similarity and filtering.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

from .models import (
    ResumeData, JobDescription, MatchResult, SearchQuery, SearchResults,
    ProcessingStatus
)
from .embedding_store import EmbeddingStore
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """Criteria for filtering resumes."""
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    required_skills: List[str] = None
    similarity_threshold: float = 0.7
    
    def __post_init__(self):
        if self.required_skills is None:
            self.required_skills = []


class ResumeFilter:
    """
    Filters resumes based on various criteria.
    """
    
    def __init__(self):
        """Initialize the resume filter."""
        pass
    
    def check_experience_match(
        self, 
        resume_experience: Optional[float],
        min_required: Optional[float] = None,
        max_required: Optional[float] = None
    ) -> bool:
        """
        Check if resume experience matches requirements.
        
        Args:
            resume_experience: Years of experience from resume
            min_required: Minimum required experience
            max_required: Maximum required experience
            
        Returns:
            True if experience matches requirements
        """
        if resume_experience is None:
            # If no experience info, assume it passes (benefit of doubt)
            return True
        
        if min_required is not None and resume_experience < min_required:
            return False
        
        if max_required is not None and resume_experience > max_required:
            # Allow some flexibility for overqualified candidates
            return resume_experience <= max_required + 2
        
        return True
    
    def check_skills_match(
        self, 
        resume_skills: List[str],
        required_skills: List[str],
        match_threshold: float = 0.5
    ) -> Dict[str, bool]:
        """
        Check which required skills are matched by the resume.
        
        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from JD
            match_threshold: Minimum percentage of required skills to match
            
        Returns:
            Dictionary mapping each required skill to match status
        """
        if not required_skills:
            return {}
        
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        skills_match = {}
        
        for required_skill in required_skills:
            # Exact match
            if required_skill.lower() in resume_skills_lower:
                skills_match[required_skill] = True
                continue
            
            # Partial match (for compound skills)
            partial_match = False
            for resume_skill in resume_skills_lower:
                if (required_skill.lower() in resume_skill or 
                    resume_skill in required_skill.lower()):
                    partial_match = True
                    break
            
            skills_match[required_skill] = partial_match
        
        return skills_match
    
    def calculate_skills_score(
        self, 
        skills_match: Dict[str, bool],
        required_skills: List[str],
        preferred_skills: List[str] = None
    ) -> float:
        """
        Calculate a skills matching score.
        
        Args:
            skills_match: Dictionary of skill matches
            required_skills: List of required skills
            preferred_skills: List of preferred skills
            
        Returns:
            Skills score between 0 and 1
        """
        if not required_skills:
            return 1.0
        
        # Calculate required skills score (weighted 70%)
        required_matches = sum(1 for skill in required_skills 
                             if skills_match.get(skill, False))
        required_score = required_matches / len(required_skills) if required_skills else 1.0
        
        # Calculate preferred skills score (weighted 30%)
        preferred_score = 0.0
        if preferred_skills:
            resume_skills_lower = set(skill.lower() for skill in skills_match.keys())
            preferred_matches = sum(1 for skill in preferred_skills 
                                  if skill.lower() in resume_skills_lower)
            preferred_score = preferred_matches / len(preferred_skills)
        
        # Combine scores
        total_score = (required_score * 0.7) + (preferred_score * 0.3)
        return min(total_score, 1.0)
    
    def filter_resumes(
        self,
        resume_ids: List[str],
        resume_metadata: Dict[str, Dict[str, Any]],
        criteria: FilterCriteria
    ) -> List[str]:
        """
        Filter resume IDs based on criteria.
        
        Args:
            resume_ids: List of resume IDs to filter
            resume_metadata: Metadata for each resume
            criteria: Filter criteria
            
        Returns:
            List of filtered resume IDs
        """
        filtered_ids = []
        
        for resume_id in resume_ids:
            metadata = resume_metadata.get(resume_id, {})
            
            # Check experience
            if not self.check_experience_match(
                metadata.get('years_of_experience'),
                criteria.min_experience,
                criteria.max_experience
            ):
                continue
            
            # Check skills
            resume_skills = metadata.get('skills', [])
            skills_match = self.check_skills_match(resume_skills, criteria.required_skills)
            
            # Calculate minimum required skills match rate
            if criteria.required_skills:
                match_rate = sum(skills_match.values()) / len(criteria.required_skills)
                if match_rate < 0.3:  # At least 30% of required skills should match
                    continue
            
            filtered_ids.append(resume_id)
        
        return filtered_ids


class ResumeMatcher:
    """
    Main resume matching engine.
    Combines vector similarity search with rule-based filtering.
    """
    
    def __init__(self, embedding_store: EmbeddingStore):
        """
        Initialize the resume matcher.
        
        Args:
            embedding_store: EmbeddingStore instance for vector search
        """
        self.embedding_store = embedding_store
        self.filter = ResumeFilter()
    
    def search_matching_resumes(self, query: SearchQuery) -> SearchResults:
        """
        Search for resumes matching a job description.
        
        Args:
            query: Search query with JD and criteria
            
        Returns:
            SearchResults with matched resumes
        """
        start_time = time.time()
        
        # Get JD from somewhere (this would typically come from database)
        # For now, we'll assume it's provided in the query or retrieved separately
        jd = self._get_job_description(query.jd_id)
        if not jd:
            logger.error(f"Job description not found: {query.jd_id}")
            return SearchResults(
                query=query,
                total_matches=0,
                results=[],
                search_time_ms=0
            )
        
        # Step 1: Vector similarity search
        resume_ids, similarity_scores = self.embedding_store.search_similar_resumes(
            jd, 
            k=query.top_k,
            threshold=query.similarity_threshold
        )
        
        logger.info(f"Vector search found {len(resume_ids)} similar resumes")
        
        # Step 2: Apply filters
        if resume_ids:
            filter_criteria = FilterCriteria(
                min_experience=query.min_experience,
                max_experience=query.max_experience,
                required_skills=query.required_skills,
                similarity_threshold=query.similarity_threshold
            )
            
            # Get resume metadata for filtering
            resume_metadata = {}
            for resume_id in resume_ids:
                metadata = self.embedding_store.get_resume_metadata(resume_id)
                if metadata:
                    resume_metadata[resume_id] = metadata
            
            # Apply filters
            filtered_resume_ids = self.filter.filter_resumes(
                resume_ids, resume_metadata, filter_criteria
            )
            
            # Update similarity scores for filtered results
            filtered_scores = []
            filtered_ids = []
            for i, resume_id in enumerate(resume_ids):
                if resume_id in filtered_resume_ids:
                    filtered_ids.append(resume_id)
                    filtered_scores.append(similarity_scores[i])
            
            resume_ids = filtered_ids
            similarity_scores = filtered_scores
        
        logger.info(f"After filtering: {len(resume_ids)} resumes remain")
        
        # Step 3: Create match results
        match_results = []
        for resume_id, similarity_score in zip(resume_ids, similarity_scores):
            metadata = resume_metadata.get(resume_id, {})
            
            # Calculate skills match
            resume_skills = metadata.get('skills', [])
            skills_match = self.filter.check_skills_match(
                resume_skills, 
                jd.required_skills
            )
            
            # Check experience match
            experience_match = self.filter.check_experience_match(
                metadata.get('years_of_experience'),
                jd.min_experience,
                jd.max_experience
            )
            
            match_result = MatchResult(
                resume_id=resume_id,
                jd_id=query.jd_id,
                similarity_score=similarity_score,
                skills_match=skills_match,
                experience_match=experience_match
            )
            
            match_results.append(match_result)
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResults(
            query=query,
            total_matches=len(match_results),
            results=match_results,
            search_time_ms=search_time
        )
    
    def _get_job_description(self, jd_id: str) -> Optional[JobDescription]:
        """
        Get job description by ID.
        This is a placeholder - in real implementation, this would fetch from database.
        
        Args:
            jd_id: Job description ID
            
        Returns:
            JobDescription object or None
        """
        # This would typically fetch from database
        # For now, return None - this should be implemented based on your storage
        logger.warning(f"Job description retrieval not implemented for ID: {jd_id}")
        return None
    
    def rank_resumes_by_relevance(
        self, 
        match_results: List[MatchResult],
        jd: JobDescription
    ) -> List[MatchResult]:
        """
        Rank resumes by overall relevance score.
        
        Args:
            match_results: List of match results
            jd: Job description
            
        Returns:
            Sorted list of match results
        """
        def calculate_relevance_score(match_result: MatchResult) -> float:
            """Calculate overall relevance score for a match result."""
            # Base similarity score (50% weight)
            similarity_weight = 0.5
            similarity_score = match_result.similarity_score * similarity_weight
            
            # Skills match score (30% weight)
            skills_weight = 0.3
            if match_result.skills_match:
                skills_score = sum(match_result.skills_match.values()) / len(match_result.skills_match)
            else:
                skills_score = 0.5  # Neutral if no required skills
            skills_score *= skills_weight
            
            # Experience match score (20% weight)
            experience_weight = 0.2
            experience_score = 1.0 if match_result.experience_match else 0.5
            experience_score *= experience_weight
            
            return similarity_score + skills_score + experience_score
        
        # Calculate relevance scores and sort
        scored_results = []
        for result in match_results:
            relevance_score = calculate_relevance_score(result)
            scored_results.append((relevance_score, result))
        
        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for _, result in scored_results]
    
    def get_top_candidates(
        self, 
        query: SearchQuery,
        max_candidates: int = None
    ) -> List[MatchResult]:
        """
        Get top candidates for a job description.
        
        Args:
            query: Search query
            max_candidates: Maximum number of candidates to return
            
        Returns:
            List of top match results
        """
        max_candidates = max_candidates or query.max_gpt_resumes
        
        # Search for matching resumes
        search_results = self.search_matching_resumes(query)
        
        if not search_results.results:
            return []
        
        # Get JD for ranking
        jd = self._get_job_description(query.jd_id)
        if not jd:
            # If can't get JD, just return top results by similarity
            return search_results.results[:max_candidates]
        
        # Rank by relevance
        ranked_results = self.rank_resumes_by_relevance(search_results.results, jd)
        
        # Return top candidates
        return ranked_results[:max_candidates]
    
    def get_matching_statistics(self, query: SearchQuery) -> Dict[str, Any]:
        """
        Get statistics about matching results.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with matching statistics
        """
        search_results = self.search_matching_resumes(query)
        
        if not search_results.results:
            return {
                'total_matches': 0,
                'avg_similarity': 0.0,
                'skills_coverage': {},
                'experience_distribution': {}
            }
        
        # Calculate statistics
        similarities = [result.similarity_score for result in search_results.results]
        avg_similarity = sum(similarities) / len(similarities)
        
        # Skills coverage
        skills_coverage = {}
        jd = self._get_job_description(query.jd_id)
        if jd and jd.required_skills:
            for skill in jd.required_skills:
                matches = sum(1 for result in search_results.results 
                            if result.skills_match.get(skill, False))
                skills_coverage[skill] = {
                    'matches': matches,
                    'percentage': (matches / len(search_results.results)) * 100
                }
        
        # Experience distribution
        experience_matches = sum(1 for result in search_results.results 
                               if result.experience_match)
        
        return {
            'total_matches': len(search_results.results),
            'avg_similarity': avg_similarity,
            'max_similarity': max(similarities),
            'min_similarity': min(similarities),
            'skills_coverage': skills_coverage,
            'experience_matches': experience_matches,
            'experience_match_rate': (experience_matches / len(search_results.results)) * 100,
            'search_time_ms': search_results.search_time_ms
        }


# Convenience functions
def create_search_query(
    jd_id: str,
    top_k: int = 500,
    similarity_threshold: float = 0.7,
    required_skills: List[str] = None,
    min_experience: float = None,
    max_experience: float = None,
    enable_gpt_analysis: bool = True,
    max_gpt_resumes: int = 100
) -> SearchQuery:
    """Create a search query with the specified parameters."""
    return SearchQuery(
        jd_id=jd_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        required_skills=required_skills or [],
        min_experience=min_experience,
        max_experience=max_experience,
        enable_gpt_analysis=enable_gpt_analysis,
        max_gpt_resumes=max_gpt_resumes
    )


def match_resumes_to_jd(
    embedding_store: EmbeddingStore,
    jd_id: str,
    **kwargs
) -> SearchResults:
    """Match resumes to a job description using default settings."""
    matcher = ResumeMatcher(embedding_store)
    query = create_search_query(jd_id, **kwargs)
    return matcher.search_matching_resumes(query)
