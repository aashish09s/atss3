"""
Resume Analysis Module
Generates detailed analysis and suggestions using rule-based NLP (no AI dependency).
"""

import json
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import asdict
import time
import re

from .models import (
    ResumeData, JobDescription, MatchResult, GPTAnalysis,
    ProcessingStatus
)
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiSuggestionsGenerator:
    """
    Generates detailed resume analysis and suggestions using Google Gemini API.
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Gemini suggestions generator.
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model or settings.gemini_model
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        # Usage tracking
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors': 0
        }
        
        logger.info(f"Initialized GeminiSuggestionsGenerator with model: {self.model_name}")
    
    async def analyze_resume_for_jd(
        self, 
        resume: ResumeData, 
        jd: JobDescription
    ) -> GPTAnalysis:
        """
        Analyze a single resume against a job description.
        
        Args:
            resume: ResumeData object
            jd: JobDescription object
            
        Returns:
            GPTAnalysis with detailed analysis
        """
        prompt = self._create_analysis_prompt(resume, jd)
        
        try:
            start_time = time.time()
            
            # Make API call in thread pool to avoid blocking
            def _make_request():
                response = self.model.generate_content(prompt)
                return response.text
            
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(None, _make_request)
            
            # Parse response
            analysis = self._parse_analysis_response(response_text)
            
            # Update usage stats
            self.usage_stats['total_requests'] += 1
            # Note: Gemini doesn't provide token count in response, so we estimate
            estimated_tokens = len(prompt.split()) + len(response_text.split())
            self.usage_stats['total_tokens'] += estimated_tokens
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Gemini analysis completed in {processing_time:.2f}ms")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            self.usage_stats['errors'] += 1
            
            # Return fallback analysis
            return self._create_fallback_analysis(resume, jd)
    
    def _create_analysis_prompt(self, resume: ResumeData, jd: JobDescription) -> str:
        """Create a detailed prompt for resume analysis."""
        return f"""
        You are an expert HR recruiter and technical interviewer. Analyze the following resume against the job description and provide a comprehensive assessment.

        JOB DESCRIPTION:
        Title: {jd.title}
        Company: {jd.company or 'Not specified'}
        
        Required Skills: {', '.join(jd.required_skills) if jd.required_skills else 'Not specified'}
        Preferred Skills: {', '.join(jd.preferred_skills) if jd.preferred_skills else 'Not specified'}
        Experience Required: {jd.min_experience or 'Not specified'} years
        
        Description: {jd.description[:2000]}

        CANDIDATE RESUME:
        Name: {resume.name or 'Not specified'}
        Email: {resume.email or 'Not specified'}
        Phone: {resume.phone or 'Not specified'}
        Experience: {resume.years_of_experience or 'Not specified'} years
        
        Skills: {', '.join(resume.skills) if resume.skills else 'Not specified'}
        
        Resume Text: {resume.raw_text[:3000]}

        Please provide a detailed analysis in the following JSON format:
        {{
            "match_percentage": <number between 0-100>,
            "missing_skills": ["list of missing required skills"],
            "strengths": ["list of candidate's key strengths"],
            "improvement_suggestions": ["list of suggestions for the candidate"],
            "overall_assessment": "detailed assessment paragraph",
            "technical_fit": "assessment of technical skills match",
            "experience_fit": "assessment of experience level match",
            "recommendation": "HIRE/MAYBE/NO with brief reasoning",
            "interview_questions": ["list of 3-5 relevant interview questions"]
        }}

        Focus on:
        1. Technical skills alignment
        2. Experience level appropriateness
        3. Cultural fit indicators
        4. Growth potential
        5. Specific areas for improvement

        Be objective, constructive, and provide actionable insights.
        """
    
    def _parse_analysis_response(self, response_text: str) -> GPTAnalysis:
        """Parse Gemini response into GPTAnalysis object."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # If no JSON found, try to parse the entire response
                analysis_data = json.loads(response_text)
            
            return GPTAnalysis(
                match_percentage=analysis_data.get('match_percentage', 0),
                missing_skills=analysis_data.get('missing_skills', []),
                strengths=analysis_data.get('strengths', []),
                improvement_suggestions=analysis_data.get('improvement_suggestions', []),
                overall_assessment=analysis_data.get('overall_assessment', 'Analysis not available'),
                technical_fit=analysis_data.get('technical_fit'),
                experience_fit=analysis_data.get('experience_fit'),
                recommendation=analysis_data.get('recommendation'),
                interview_questions=analysis_data.get('interview_questions', []),
                ai_model_used=self.model_name,
                tokens_used=None,  # Gemini doesn't provide this
                cost_estimate=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return self._create_fallback_analysis(None, None)
    
    def _create_fallback_analysis(self, resume: ResumeData, jd: JobDescription) -> GPTAnalysis:
        """Create a fallback analysis when Gemini fails."""
        return GPTAnalysis(
            match_percentage=50,  # Neutral score
            missing_skills=[],
            strengths=["Analysis temporarily unavailable"],
            improvement_suggestions=["Please try again later"],
            overall_assessment="AI analysis is temporarily unavailable. Please review manually.",
            technical_fit="Unable to assess",
            experience_fit="Unable to assess",
            recommendation="MANUAL_REVIEW",
            interview_questions=[],
            ai_model_used=self.model_name,
            tokens_used=0,
            cost_estimate=0.0
        )
    
    async def enhance_match_results(
        self,
        match_results: List[MatchResult],
        resume_data: Dict[str, ResumeData],
        jd: JobDescription,
        max_resumes: int = 100
    ) -> List[MatchResult]:
        """
        Enhance match results with Gemini analysis.
        
        Args:
            match_results: List of match results
            resume_data: Dictionary of resume data by ID
            jd: Job description
            max_resumes: Maximum number of resumes to analyze
            
        Returns:
            Enhanced match results with GPT analysis
        """
        if not match_results:
            return match_results
        
        # Limit the number of resumes to analyze
        resumes_to_analyze = match_results[:max_resumes]
        
        logger.info(f"Enhancing {len(resumes_to_analyze)} match results with Gemini analysis")
        
        # Process resumes in parallel (but limit concurrency)
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def analyze_single_match(match_result: MatchResult) -> MatchResult:
            async with semaphore:
                resume = resume_data.get(match_result.resume_id)
                if resume:
                    try:
                        analysis = await self.analyze_resume_for_jd(resume, jd)
                        match_result.gpt_analysis = analysis
                    except Exception as e:
                        logger.error(f"Error analyzing resume {match_result.resume_id}: {e}")
                        match_result.gpt_analysis = self._create_fallback_analysis(resume, jd)
                else:
                    logger.warning(f"Resume data not found for ID: {match_result.resume_id}")
                    match_result.gpt_analysis = self._create_fallback_analysis(None, jd)
                
                return match_result
        
        # Analyze all resumes concurrently
        enhanced_results = await asyncio.gather(
            *[analyze_single_match(match) for match in resumes_to_analyze],
            return_exceptions=True
        )
        
        # Filter out exceptions and combine with non-analyzed results
        final_results = []
        for i, result in enumerate(enhanced_results):
            if isinstance(result, Exception):
                logger.error(f"Exception in analysis {i}: {result}")
                final_results.append(match_results[i])  # Use original result
            else:
                final_results.append(result)
        
        # Add remaining results without analysis
        final_results.extend(match_results[max_resumes:])
        
        logger.info(f"Enhanced {len(final_results)} match results")
        return final_results
    
    def get_analysis_summary(self, match_results: List[MatchResult]) -> Dict[str, Any]:
        """
        Get summary statistics from match results.
        
        Args:
            match_results: List of match results with GPT analysis
            
        Returns:
            Dictionary with summary statistics
        """
        if not match_results:
            return {
                'total_analyzed': 0,
                'average_match_percentage': 0,
                'hire_recommendations': 0,
                'maybe_recommendations': 0,
                'no_recommendations': 0,
                'top_strengths': [],
                'common_missing_skills': []
            }
        
        analyzed_results = [r for r in match_results if r.gpt_analysis]
        
        if not analyzed_results:
            return {
                'total_analyzed': 0,
                'average_match_percentage': 0,
                'hire_recommendations': 0,
                'maybe_recommendations': 0,
                'no_recommendations': 0,
                'top_strengths': [],
                'common_missing_skills': []
            }
        
        # Calculate statistics
        match_percentages = [r.gpt_analysis.match_percentage for r in analyzed_results]
        average_match = sum(match_percentages) / len(match_percentages)
        
        # Count recommendations
        hire_count = sum(1 for r in analyzed_results if r.gpt_analysis.recommendation == "HIRE")
        maybe_count = sum(1 for r in analyzed_results if r.gpt_analysis.recommendation == "MAYBE")
        no_count = sum(1 for r in analyzed_results if r.gpt_analysis.recommendation == "NO")
        
        # Collect strengths and missing skills
        all_strengths = []
        all_missing_skills = []
        
        for result in analyzed_results:
            all_strengths.extend(result.gpt_analysis.strengths)
            all_missing_skills.extend(result.gpt_analysis.missing_skills)
        
        # Get most common items
        from collections import Counter
        top_strengths = [item for item, count in Counter(all_strengths).most_common(5)]
        common_missing_skills = [item for item, count in Counter(all_missing_skills).most_common(5)]
        
        return {
            'total_analyzed': len(analyzed_results),
            'average_match_percentage': round(average_match, 2),
            'hire_recommendations': hire_count,
            'maybe_recommendations': maybe_count,
            'no_recommendations': no_count,
            'top_strengths': top_strengths,
            'common_missing_skills': common_missing_skills
        }
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for the Gemini API."""
        return self.usage_stats.copy()


class ResumeAnalysisService:
    """
    High-level service for resume analysis using Gemini.
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize the analysis service."""
        self.gemini_generator = GeminiSuggestionsGenerator(api_key, model)
    
    async def analyze_resume_for_jd(self, resume: ResumeData, jd: JobDescription) -> GPTAnalysis:
        """Analyze a single resume against a job description."""
        return await self.gemini_generator.analyze_resume_for_jd(resume, jd)
    
    async def enhance_match_results(
        self,
        match_results: List[MatchResult],
        resume_data: Dict[str, ResumeData],
        jd: JobDescription,
        max_resumes: int = 100
    ) -> List[MatchResult]:
        """Enhance match results with Gemini analysis."""
        return await self.gemini_generator.enhance_match_results(
            match_results, resume_data, jd, max_resumes
        )
    
    def get_analysis_summary(self, match_results: List[MatchResult]) -> Dict[str, Any]:
        """Get summary statistics from match results."""
        return self.gemini_generator.get_analysis_summary(match_results)
