import json
import re
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

OLLAMA_HOST = settings.ollama_base_url
MODEL = settings.ollama_model_name

SYSTEM_PROMPT = """
You are an expert ATS (Applicant Tracking System) resume parser with 10+ years of experience.
Your task is to extract structured information from resumes with maximum accuracy.

OUTPUT FORMAT

Return ONLY a single valid JSON object.
No explanation, no markdown, no code blocks.
Start your response with { and end with }.

JSON SCHEMA (follow exactly)
{
  "personal": {
    "name": "Full name or null",
    "email": "email@example.com or null",
    "phone": "phone number as string or null",
    "location": "City, State/Country or null",
    "linkedin": "full LinkedIn URL or username or null",
    "github": "full GitHub URL or username or null",
    "portfolio": "portfolio/website URL or null"
  },
  "summary": "Professional summary paragraph or null",
  "current_role": "Most recent job title or null",
  "years_experience": <integer: total years of professional work experience, 0 if fresher>,
  "experience": [
    {
      "title": "Job title",
      "company": "Company/Organization name",
      "location": "City, Country or null",
      "duration": "e.g. Jan 2022 - Mar 2024",
      "duration_months": <integer: approximate months in this role>,
      "highlights": ["bullet point 1", "bullet point 2"]
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "duration": "e.g. Mar 2023 - May 2023 or null",
      "tech_stack": ["tech1", "tech2"],
      "highlights": ["what was built", "impact or result"]
    }
  ],
  "education": [
    {
      "degree": "Full degree name e.g. B.Tech Computer Science",
      "institution": "College/University name",
      "location": "City, Country or null",
      "year": "Graduation year or expected year e.g. 2024",
      "cgpa_or_percentage": "e.g. 8.5 CGPA or 85% or null"
    }
  ],
  "skills": {
    "technical": [],
    "soft": [],
    "languages": [],
    "domain": []
  }, // IMPORTANT: Return only the core skill name without any parenthetical descriptions. For example write 'NLP' not 'NLP (NLTK / SpaCy)', write 'SQL' not 'SQL (Data Querying)'
  "certifications": [
    {
      "name": "Certification name",
      "issuer": "Issuing organization or null",
      "year": "Year or null"
    }
  ],
  "achievements": [],
  "languages_spoken": []
}


STRICT EXTRACTION RULES

[RULE 1 - SKILLS: ONE PER ELEMENT]
Each array element = exactly ONE skill. Never combine multiple skills in one string.
✅ CORRECT: ["Python", "NumPy", "Data Analysis", "SQL"]
❌ WRONG:   ["Python, NumPy", "Data Analysis, SQL"]

[RULE 2 - EXPERIENCE vs PROJECTS]
"experience" → ONLY real jobs/internships with a named employer (paid or unpaid)
"projects"   → personal projects, academic/capstone projects, hackathon projects, freelance work
When in doubt: if there is a company name + role title = experience. Otherwise = project.

[RULE 3 - SKILLS: SCAN ENTIRE RESUME]
Extract skills mentioned ANYWHERE: summary, experience bullets, project descriptions, skills section.
Classify into:
  "technical"  → tools, libraries, frameworks, programming languages, software
                 e.g. Python, TensorFlow, MySQL, Docker, React, Excel
  "domain"     → knowledge areas and methodologies
                 e.g. Machine Learning, Deep Learning, NLP, Computer Vision, Data Analysis,
                      Data Preprocessing, Feature Engineering, EDA, Data Visualization,
                      Statistical Analysis, Predictive Modeling, Model Evaluation,
                      Time Series Analysis, ETL, Data Cleaning, A/B Testing,
                      Object Detection, Transfer Learning
  "soft"       → interpersonal/professional skills
                 e.g. Leadership, Communication, Problem Solving, Team Collaboration
  "languages"  → programming/query languages ONLY
                 e.g. Python, Java, SQL, C++, JavaScript
  NOTE: A language like Python can appear in BOTH "technical" and "languages". That is correct.

[RULE 4 - YEARS EXPERIENCE]
Calculate from earliest work experience start date to present (or last end date).
Internships COUNT. Part-time jobs COUNT. Freelance work COUNTS.
If only education/projects exist, set years_experience = 0.
Round to nearest integer (e.g. 2.5 years → 2 or 3).

[RULE 5 - MISSING FIELDS]
If a field cannot be found anywhere in the resume, set it to:
  - Use actual null (not the string "null") for missing values.
  - null        → for string/object fields
  - []          → for array fields
  - 0           → for years_experience only
Never guess, invent, or hallucinate any information.

[RULE 6 - CLEAN TEXT]
Remove excessive whitespace, bullet characters (•, -, *, ▪), and special symbols from text.
Keep technical terms, abbreviations, and proper nouns exactly as written.

[RULE 7 - DATES]
Preserve original date format from resume (e.g. "Jan 2023", "2022-2024", "Present").
Use "Present" for current roles. Do not convert or reformat dates.

[RULE 8 - SUMMARY]
Extract "summary" ONLY from these sources (in priority order):
  1. A section explicitly labeled: "Summary", "Professional Summary", 
     "Profile", "Objective", "About Me", "Career Objective"
  2. If no such section exists, use the first 2-3 sentences from the 
     resume that describe the candidate professionally.
"""
# SYSTEM_PROMPT = """
# You are an expert resume parser.

# Extract structured information from the resume and return ONLY valid JSON.

# Structure:
# {
#   "personal": {
#     "name": "",
#     "email": "",
#     "phone": "",
#     "location": "",
#     "linkedin": "",
#     "github": ""
#   },
#   "summary": "",
#   "current_role": "",
#   "years_experience": 0,
#   "experience": [
#     {
#       "title": "",
#       "company": "",
#       "duration": "",
#       "highlights": []
#     }
#   ],
#   "projects": [
#     {
#       "name": "",
#       "duration": "",
#       "highlights": []
#     }
#   ],
#   "education": [
#     {
#       "degree": "",
#       "institution": "",
#       "year": ""
#     }
#   ],
#   "skills": {
#     "technical": [],
#     "soft": [],
#     "languages": []
#   },


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Clean LLM/Ollama response and return parsed JSON.

    Tries multiple strategies so that small formatting issues from the model
    (extra ``` wrappers, {{ }}, trailing commas, etc.) don't break parsing.
    """
    if not (text or "").strip():
        raise ValueError("Empty response from model")

    cleaned = text.strip()

    # Remove markdown code fences if present
    cleaned = re.sub(r"```json", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)

    # Fix Ollama template artifact: {{ }} -> { }
    cleaned = cleaned.replace("{{", "{").replace("}}", "}")

    # Try to isolate a well-formed outer JSON object using brace depth counting
    start = cleaned.find("{")
    if start == -1:
        print(f"[OLLAMA PARSER] No JSON object in response. First 400 chars: {repr(text[:400])}")
        raise ValueError("No JSON object found in model response")

    depth = 0
    end = None
    for i, ch in enumerate(cleaned[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end is None or end <= start:
        print(f"[OLLAMA PARSER] Could not find matching closing brace. First 400 chars: {repr(text[:400])}")
        raise ValueError("No complete JSON object found in model response")

    cleaned = cleaned[start : end + 1]

    # Fix common JSON issues: trailing commas before } or ]
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*]", "]", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Last-resort attempt: regex to grab a JSON-looking block
        print(f"[OLLAMA PARSER] Primary JSON decode error: {e}. Trying regex extraction.")
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e2:
                print(f"[OLLAMA PARSER] Regex JSON decode error: {e2}. Fragment: {repr(candidate[:300])}")
        else:
            print(f"[OLLAMA PARSER] Regex could not find JSON block. Fragment: {repr(cleaned[:300])}")
        # If everything fails, re-raise the original error
        raise

# def _extract_json(text: str) -> Dict[str, Any]:
#     """
#     Clean LLM response and return parsed JSON.

#     Mirrors the logic used in `updates/mps.py` but adapted for reuse here.
#     """
#     if not (text or "").strip():
#         raise ValueError("Empty response from model")
#     cleaned = re.sub(r"```json", "", text, flags=re.IGNORECASE)
#     cleaned = re.sub(r"```", "", cleaned)

#     start = cleaned.find("{")
#     end = cleaned.rfind("}")

#     if start == -1 or end == -1 or end <= start:
#         print(f"[OLLAMA PARSER] No JSON object in response. First 400 chars: {repr(text[:400])}")
#         raise ValueError("No JSON object found in model response")

#     cleaned = cleaned[start : end + 1]
#     # Fix common LLM JSON issues: trailing commas, single quotes
#     cleaned = re.sub(r",\s*}", "}", cleaned)
#     cleaned = re.sub(r",\s*]", "]", cleaned)

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError as e:
#         print(f"[OLLAMA PARSER] JSON decode error: {e}. Fragment: {repr(cleaned[:300])}")
#         raise


def _call_ollama(resume_text: str) -> str:
    """Call local Ollama chat endpoint and return raw content."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": resume_text},
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 2048,
        },
    }

    resp = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json=payload,
        timeout=600,
    ) 
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content", "") or ""


def parse_resume_with_ollama(text_content: str) -> Optional[Dict[str, Any]]:
    """
    Parse raw resume text using the local Ollama model.

    Returns parsed JSON dict on success, or None on any failure.
    """
    try:
        raw = _call_ollama(text_content)
        if not raw or not raw.strip():
            print("[OLLAMA PARSER] Empty response from Ollama (model may have returned nothing).")
            return None
        print(f"[OLLAMA PARSER] Raw response length: {len(raw)}, first 200 chars: {repr(raw[:200])}")
        out = _extract_json(raw)
        print(f"[OLLAMA PARSER] Parsed keys: {list(out.keys()) if out else None}")
        return out
    except requests.exceptions.RequestException as e:
        print(f"[OLLAMA PARSER] Ollama request failed (is Ollama running?): {e}")
        return None
    except Exception as e:
        print(f"[OLLAMA PARSER] Failed to parse with Ollama: {e}")
        import traceback
        traceback.print_exc()
        return None

