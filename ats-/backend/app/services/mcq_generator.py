import json
import re
import requests
from typing import List, Dict, Any, Optional
from app.core.config import settings

OLLAMA_HOST = settings.ollama_base_url
MODEL = settings.ollama_model_name


def _clean_json(text: str) -> str:
    text = text.strip()
    # Remove markdown code blocks if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def generate_mcqs_with_ollama(jd_title: str, jd_description: str, count: int = 10) -> List[Dict]:
    """Generate MCQ questions from JD using Ollama"""
    prompt = f"""You are an expert technical interviewer. Generate exactly {count} multiple choice questions (MCQs) based on this job description.

Job Title: {jd_title}
Job Description: {jd_description[:2000]}

Rules:
- Questions must test knowledge relevant to this specific role
- Each question must have exactly 4 options (A, B, C, D)
- Only one option is correct
- Questions should range from basic to intermediate difficulty
- Return ONLY valid JSON, no explanation, no markdown

Return this exact JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text", 
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "topic": "topic name"
    }}
  ]
}}"""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 3000,
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            raw = response.json().get("response", "")
            cleaned = _clean_json(raw)
            # Extract JSON from response
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group())
                questions = data.get("questions", [])
                if questions and len(questions) > 0:
                    return questions[:count]
    except Exception as e:
        print(f"[MCQ] Ollama error: {e}")
    
    return []


async def generate_mcqs_with_gemini(jd_title: str, jd_description: str, count: int = 10) -> List[Dict]:
    """Generate MCQ questions from JD using Gemini as fallback"""
    try:
        import google.generativeai as genai
        if not settings.gemini_api_key:
            return []
        
        genai.configure(api_key=settings.gemini_api_key)
        
        prompt = f"""You are an expert technical interviewer. Generate exactly {count} multiple choice questions (MCQs) based on this job description.

Job Title: {jd_title}
Job Description: {jd_description[:2000]}

Rules:
- Questions must test knowledge relevant to this specific role
- Each question must have exactly 4 options (A, B, C, D)
- Only one option is correct
- Questions should range from basic to intermediate difficulty
- Return ONLY valid JSON, no explanation, no markdown

Return this exact JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "topic": "topic name"
    }}
  ]
}}"""

        for model_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                raw = response.text
                cleaned = _clean_json(raw)
                match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    questions = data.get("questions", [])
                    if questions:
                        return questions[:count]
                break
            except Exception:
                continue
    except Exception as e:
        print(f"[MCQ] Gemini error: {e}")
    
    return []


def get_fallback_mcqs(jd_title: str, count: int = 10) -> List[Dict]:
    """Fallback generic MCQs if AI fails"""
    generic = [
        {
            "id": 1,
            "question": f"What is the primary responsibility of a {jd_title}?",
            "options": {"A": "Managing finances", "B": "Performing role-specific technical tasks", "C": "HR management", "D": "Marketing"},
            "correct_answer": "B",
            "topic": "Role Understanding"
        },
        {
            "id": 2,
            "question": "Which of the following best describes agile methodology?",
            "options": {"A": "Waterfall development", "B": "Iterative and incremental development", "C": "Documentation-heavy process", "D": "Single release cycle"},
            "correct_answer": "B",
            "topic": "Methodology"
        },
        {
            "id": 3,
            "question": "What does 'version control' mean in software development?",
            "options": {"A": "Tracking software licenses", "B": "Managing code changes over time", "C": "Versioning APIs", "D": "Updating software packages"},
            "correct_answer": "B",
            "topic": "General"
        },
        {
            "id": 4,
            "question": "Which is a key soft skill for professional success?",
            "options": {"A": "Avoiding collaboration", "B": "Effective communication", "C": "Working in isolation", "D": "Ignoring feedback"},
            "correct_answer": "B",
            "topic": "Soft Skills"
        },
        {
            "id": 5,
            "question": "What is the purpose of code review?",
            "options": {"A": "Slow down development", "B": "Identify bugs and improve quality", "C": "Replace testing", "D": "Avoid documentation"},
            "correct_answer": "B",
            "topic": "Best Practices"
        },
    ]
    return generic[:count]
