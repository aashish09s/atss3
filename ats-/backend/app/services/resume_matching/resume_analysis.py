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
from math import isfinite

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import (
    ResumeData, JobDescription, MatchResult, GPTAnalysis,
    ProcessingStatus
)
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeAnalysisService:
    """
    Generates detailed resume analysis and suggestions using rule-based NLP (no AI dependency).
    """
    
    def __init__(self):
        """
        Initialize resume analysis service.
        """
        # Skills database for analysis
        self.skills_database = self._load_skills_database()
        
        # Analysis patterns
        self.strength_indicators = [
            "expert", "senior", "lead", "principal", "architect", "manager",
            "years of experience", "proficient", "advanced", "expertise",
            "certified", "specialized", "mastered", "optimized", "improved"
        ]
        
        self.improvement_indicators = [
            "basic", "beginner", "learning", "familiar", "entry-level",
            "junior", "assistant", "intern", "trainee", "new to"
        ]
        
        logger.info("Initialized ResumeAnalysisService with rule-based analysis")
    
    def _load_skills_database(self) -> Dict[str, str]:
        """Load comprehensive skills database for analysis."""
        from .comprehensive_skills import get_all_skills
        return get_all_skills()
    
    async def analyze_resume_for_jd(
        self,
        resume: ResumeData,
        jd: JobDescription
    ) -> GPTAnalysis:
        """
        Analyze resume vs job description using a local hybrid similarity approach (no external APIs).
        Required scoring:
          - Skills: 70% Jaccard on required skills, 30% TF-IDF cosine on required skills
          - Experience: full credit if resume.years_of_experience >= jd.min_experience,
            else partial (resume/min). Missing values => neutral 0.5
          - Final match score: 70% skills + 30% experience
        Also computes strengths, weaknesses, and experience relevance summary.
        """
        try:
            start_time = time.time()

            # Normalize skills
            candidate_skills = self._normalize_skills(resume.skills)
            required_skills = self._normalize_skills(jd.required_skills)
            preferred_skills = self._normalize_skills(jd.preferred_skills)

            candidate_set = set(candidate_skills)
            required_set = set(required_skills)
            preferred_set = set(preferred_skills)
            job_total_set = required_set.union(preferred_set)

            # Strengths and weaknesses
            strengths_list = sorted(candidate_set.intersection(job_total_set))
            weaknesses_list = sorted(required_set.difference(candidate_set))

            # Skill similarity: hybrid of Jaccard (70%) and TF-IDF cosine (30%)
            jaccard = self._jaccard_similarity(candidate_set, required_set)
            cosine = self._tfidf_cosine(candidate_skills, required_skills)
            skill_score_0_1 = 0.7 * jaccard + 0.3 * cosine
            skill_match_percentage = max(0.0, min(100.0, skill_score_0_1 * 100.0))

            # Experience score (0..1)
            years = resume.years_of_experience
            min_exp = jd.min_experience
            experience_score = 0.5
            if years is not None and min_exp is not None and isfinite(years) and isfinite(min_exp):
                if min_exp <= 0:
                    experience_score = 1.0
                elif years >= min_exp:
                    experience_score = 1.0
                else:
                    experience_score = max(0.0, min(1.0, years / min_exp))
            elif years is None or min_exp is None:
                experience_score = 0.5

            # Final match score (0..100)
            final_score_0_1 = 0.7 * skill_score_0_1 + 0.3 * experience_score
            match_percentage = max(0.0, min(100.0, final_score_0_1 * 100.0))

            # Experience relevance string
            experience_relevance = self._experience_relevance_text(years, min_exp)

            # Build AI-like assessment strings mapped to existing GPTAnalysis fields
            overall_assessment = (
                f"Overall match {match_percentage:.1f}%. Skills {skill_match_percentage:.1f}%. "
                f"Experience: {experience_relevance}."
            )

            technical_fit = f"Skill match score: {skill_match_percentage:.1f}% (hybrid Jaccard+TF-IDF)"
            experience_fit = experience_relevance

            if match_percentage >= 75:
                recommendation = "Proceed to interview"
            elif match_percentage >= 55:
                recommendation = "Keep in shortlist"
            else:
                recommendation = "Consider only if pipeline is sparse"

            analysis = GPTAnalysis(
                match_percentage=round(match_percentage, 2),
                match_score=round(match_percentage, 2),
                skill_match_percentage=round(skill_match_percentage, 2),
                missing_skills=weaknesses_list,
                weaknesses=weaknesses_list,
                strengths=strengths_list,
                improvement_suggestions=[
                    "Upskill in missing required skills" if weaknesses_list else "Refine resume highlights"
                ],
                overall_assessment=overall_assessment,
                technical_fit=technical_fit,
                experience_fit=experience_fit,
                experience_relevance=experience_relevance,
                experience_in_years=years,
                recommendation=recommendation,
                interview_questions=[],
                ai_model_used="local-hybrid-similarity:v1",
                tokens_used=0,
                cost_estimate=0.0,
            )

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(
                "Hybrid similarity analysis completed in %.2fms (match=%.2f, skills=%.2f)",
                processing_time_ms,
                analysis.match_percentage,
                skill_match_percentage,
            )
            return analysis

        except Exception as e:
            logger.exception("Error in hybrid similarity analysis: %s", e)
            return self._create_fallback_analysis(resume, jd)

    def _normalize_skills(self, skills: Optional[List[str]]) -> List[str]:
        if not skills:
            return []
        normalized: List[str] = []
        for s in skills:
            if not s:
                continue
            token = re.sub(r"\s+", " ", s.strip().lower())
            if token:
                normalized.append(token)
        # De-duplicate while preserving order
        seen = set()
        unique: List[str] = []
        for t in normalized:
            if t not in seen:
                unique.append(t)
                seen.add(t)
        return unique

    def _jaccard_similarity(self, a: set, b: set) -> float:
        if not a and not b:
            return 0.0
        union_size = len(a.union(b))
        if union_size == 0:
            return 0.0
        return len(a.intersection(b)) / union_size

    def _tfidf_cosine(self, candidate_skills: List[str], required_skills: List[str]) -> float:
        if not candidate_skills or not required_skills:
            return 0.0
        # Treat each skill list as a small document
        candidate_doc = ", ".join(candidate_skills)
        required_doc = ", ".join(required_skills)
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            tfidf = vectorizer.fit_transform([candidate_doc, required_doc])
            sim_matrix = cosine_similarity(tfidf[0:1], tfidf[1:2])
            return float(sim_matrix[0, 0]) if sim_matrix.size else 0.0
        except Exception:
            return 0.0

    def _experience_relevance_text(self, years: Optional[float], min_exp: Optional[float]) -> str:
        if years is None or min_exp is None:
            return "Unknown"
        try:
            years_val = float(years)
            min_val = float(min_exp)
        except Exception:
            return "Unknown"
        if min_val <= 0:
            return f"Qualified +{years_val:.1f} year(s)" if years_val > 0 else "Qualified"
        if years_val >= min_val:
            diff = years_val - min_val
            if diff <= 0.05:  # effectively equal
                return "Qualified"
            return f"Qualified +{diff:.1f} year(s)"
        return "Underqualified"
    
    def _perform_rule_based_analysis(self, resume: ResumeData, jd: JobDescription) -> GPTAnalysis:
        """Perform comprehensive rule-based analysis."""
        
        # Calculate skill match percentage
        skill_match_percentage = self._calculate_skill_match(resume, jd)
        
        # Analyze experience relevance
        experience_analysis = self._analyze_experience_relevance(resume, jd)
        
        # Generate strengths
        strengths = self._identify_strengths(resume, jd)
        
        # Generate areas for improvement
        improvements = self._identify_improvements(resume, jd)
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            skill_match_percentage, experience_analysis, resume, jd
        )
        
        # Generate interview questions
        interview_questions = self._generate_interview_questions(resume, jd)
        
        # Calculate match score
        match_score = self._calculate_match_score(
            skill_match_percentage, experience_analysis, resume, jd
        )
        
        return GPTAnalysis(
            overall_assessment=overall_assessment,
            strengths=strengths,
            areas_for_improvement=improvements,
            skill_match_percentage=skill_match_percentage,
            experience_relevance=experience_analysis,
            interview_questions=interview_questions,
            match_score=match_score,
            reasoning="Rule-based analysis using NLP patterns and skill matching algorithms"
        )
    
    def _calculate_skill_match(self, resume: ResumeData, jd: JobDescription) -> float:
        """Calculate skill match percentage between resume and job description."""
        if not jd.required_skills:
            return 0.0
        
        resume_skills = set(skill.lower() for skill in resume.skills)
        required_skills = set(skill.lower() for skill in jd.required_skills)
        
        # Calculate exact matches
        exact_matches = len(resume_skills.intersection(required_skills))
        
        # Calculate partial matches (skills that contain required skills)
        partial_matches = 0
        for required_skill in required_skills:
            for resume_skill in resume_skills:
                if required_skill in resume_skill or resume_skill in required_skill:
                    partial_matches += 1
                    break
        
        total_matches = exact_matches + (partial_matches * 0.5)  # Partial matches count as 50%
        match_percentage = (total_matches / len(required_skills)) * 100
        
        return min(match_percentage, 100.0)  # Cap at 100%
    
    def _analyze_experience_relevance(self, resume: ResumeData, jd: JobDescription) -> str:
        """Analyze how relevant the candidate's experience is to the job."""
        if not resume.years_of_experience:
            return "No experience information available"
        
        years = resume.years_of_experience
        
        # Analyze based on years of experience
        if years >= 5:
            return f"Strong experience with {years} years in the field"
        elif years >= 2:
            return f"Moderate experience with {years} years in the field"
        elif years >= 1:
            return f"Entry-level experience with {years} year in the field"
        else:
            return "Limited professional experience"
    
    def _identify_strengths(self, resume: ResumeData, jd: JobDescription) -> List[str]:
        """Identify candidate strengths based on resume content."""
        strengths = []
        
        # Skill-based strengths
        if resume.skills:
            strengths.append(f"Technical skills: {', '.join(resume.skills[:5])}")
        
        # Experience-based strengths
        if resume.years_of_experience and resume.years_of_experience >= 3:
            strengths.append(f"Experienced professional with {resume.years_of_experience} years")
        
        # Education strengths
        if resume.raw_text:
            education_keywords = ["bachelor", "master", "phd", "degree", "university", "college"]
            if any(keyword in resume.raw_text.lower() for keyword in education_keywords):
                strengths.append("Strong educational background")
        
        # Technology strengths
        if resume.skills:
            modern_tech = ["react", "python", "aws", "docker", "kubernetes", "machine learning"]
            modern_skills = [skill for skill in resume.skills if any(tech in skill.lower() for tech in modern_tech)]
            if modern_skills:
                strengths.append(f"Modern technology expertise: {', '.join(modern_skills[:3])}")
        
        return strengths[:5]  # Limit to top 5 strengths
    
    def _identify_improvements(self, resume: ResumeData, jd: JobDescription) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        # Missing required skills
        if jd.required_skills:
            resume_skills = set(skill.lower() for skill in resume.skills)
            missing_skills = []
            for required_skill in jd.required_skills:
                if not any(required_skill.lower() in skill.lower() for skill in resume.skills):
                    missing_skills.append(required_skill)
            
            if missing_skills:
                improvements.append(f"Consider learning: {', '.join(missing_skills[:3])}")
        
        # Experience level
        if resume.years_of_experience and resume.years_of_experience < 2:
            improvements.append("Gain more hands-on experience in the field")
        
        # Education
        if resume.raw_text:
            education_keywords = ["bachelor", "master", "phd", "degree", "university", "college"]
            if not any(keyword in resume.raw_text.lower() for keyword in education_keywords):
                improvements.append("Consider pursuing relevant education or certifications")
        
        # Soft skills
        soft_skills = ["communication", "leadership", "teamwork", "problem solving", "project management"]
        if resume.raw_text:
            found_soft_skills = [skill for skill in soft_skills if skill in resume.raw_text.lower()]
            if len(found_soft_skills) < 2:
                improvements.append("Highlight more soft skills and interpersonal abilities")
        
        return improvements[:5]  # Limit to top 5 improvements
    
    def _generate_overall_assessment(self, skill_match: float, experience_analysis: str, resume: ResumeData, jd: JobDescription) -> str:
        """Generate overall assessment of the candidate."""
        assessment_parts = []
        
        # Skill match assessment
        if skill_match >= 80:
            assessment_parts.append("Excellent technical skill match")
        elif skill_match >= 60:
            assessment_parts.append("Good technical skill match")
        elif skill_match >= 40:
            assessment_parts.append("Moderate technical skill match")
        else:
            assessment_parts.append("Limited technical skill match")
        
        # Experience assessment
        assessment_parts.append(experience_analysis)
        
        # Overall recommendation
        if skill_match >= 70 and resume.years_of_experience and resume.years_of_experience >= 2:
            assessment_parts.append("Strong candidate for this position")
        elif skill_match >= 50:
            assessment_parts.append("Potential candidate with some training needed")
        else:
            assessment_parts.append("May require significant training or experience")
        
        return ". ".join(assessment_parts) + "."
    
    def _generate_interview_questions(self, resume: ResumeData, jd: JobDescription) -> List[str]:
        """Generate relevant interview questions based on resume and job description."""
        questions = []
        
        # Technical questions based on skills
        if resume.skills:
            top_skills = resume.skills[:3]
            for skill in top_skills:
                questions.append(f"Can you explain your experience with {skill}?")
        
        # Experience-based questions
        if resume.years_of_experience:
            questions.append(f"With {resume.years_of_experience} years of experience, what has been your biggest challenge?")
        
        # Job-specific questions
        if jd.required_skills:
            questions.append(f"How would you approach a project requiring {jd.required_skills[0]}?")
        
        # General questions
        questions.extend([
            "What motivates you in your career?",
            "How do you stay updated with new technologies?",
            "Describe a time when you had to learn something new quickly."
        ])
        
        return questions[:8]  # Limit to 8 questions
    
    def _calculate_match_score(self, skill_match: float, experience_analysis: str, resume: ResumeData, jd: JobDescription) -> float:
        """Calculate overall match score (0-100)."""
        base_score = skill_match * 0.6  # 60% weight on skills
        
        # Experience bonus
        experience_bonus = 0
        if resume.years_of_experience:
            if resume.years_of_experience >= 5:
                experience_bonus = 20
            elif resume.years_of_experience >= 3:
                experience_bonus = 15
            elif resume.years_of_experience >= 1:
                experience_bonus = 10
        
        # Education bonus
        education_bonus = 0
        if resume.raw_text:
            education_keywords = ["bachelor", "master", "phd", "degree"]
            if any(keyword in resume.raw_text.lower() for keyword in education_keywords):
                education_bonus = 10
        
        total_score = base_score + experience_bonus + education_bonus
        return min(total_score, 100.0)  # Cap at 100
    
    def _create_fallback_analysis(self, resume: ResumeData, jd: JobDescription) -> GPTAnalysis:
        """Create a basic fallback analysis when detailed analysis fails."""
        return GPTAnalysis(
            overall_assessment="Basic analysis completed. Manual review recommended.",
            strengths=["Resume submitted for review"],
            areas_for_improvement=["Detailed analysis unavailable"],
            skill_match_percentage=0.0,
            experience_relevance="Unable to analyze experience",
            interview_questions=["Please provide more details about your background"],
            match_score=0.0,
            reasoning="Fallback analysis due to processing error"
        )


# Convenience function for backward compatibility
async def analyze_resume_for_job(resume: ResumeData, jd: JobDescription) -> GPTAnalysis:
    """Analyze a resume against a job description."""
    service = ResumeAnalysisService()
    return await service.analyze_resume_for_jd(resume, jd)
