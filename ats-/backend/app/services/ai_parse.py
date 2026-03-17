import json
import asyncio
from typing import Dict, Any, Optional, List
import platform

# Gemini AI import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# spaCy import with platform-specific handling
try:
    if platform.system() == "Windows":
        import spacy
        # Load spaCy model lazily to avoid startup issues
        nlp = None
        SPACY_AVAILABLE = False
        
        def load_spacy_model():
            global nlp, SPACY_AVAILABLE
            if nlp is None:
                try:
                    nlp = spacy.load("en_core_web_sm")
                    SPACY_AVAILABLE = True
                except OSError:
                    SPACY_AVAILABLE = False
                    nlp = None
            return nlp
    else:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            SPACY_AVAILABLE = True
        except OSError:
            SPACY_AVAILABLE = False
            nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None

import re
from app.core.config import settings


async def _call_gemini(prompt: str) -> Optional[Dict[Any, Any]]:
    """Call Gemini AI API"""
    if not GEMINI_AVAILABLE or not settings.gemini_api_key:
        return None
    
    try:
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        # Try different model names as Google has updated their API
        model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Test if model works
                test_response = model.generate_content("Hello")
                break
            except Exception:
                continue
        
        if not model:
            raise Exception("No working Gemini model found")
        
        # Make API call in thread pool to avoid blocking
        def _make_request():
            response = model.generate_content(prompt)
            return response.text
        
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(None, _make_request)
        
        # Try to parse as JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
            
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return None


def _parse_with_spacy_text(text: str) -> Dict[Any, Any]:
    """Parse resume text using spaCy NLP (fallback method)"""
    # Try to load spaCy model lazily
    if platform.system() == "Windows":
        nlp_model = load_spacy_model()
    else:
        nlp_model = nlp
    
    if not SPACY_AVAILABLE or not nlp_model:
        return {
            "name": "Unknown",
            "email": None,
            "phone": None,
            "skills": [],
            "experience": [],
            "education": [],
            "summary": text[:2500] + "..." if len(text) > 2500 else text,  # Increased to 2500
            "location": None,
            "certifications": [],
            "projects": []
        }
    
    doc = nlp_model(text)
    
    # Extract basic information
    parsed_data = {
        "name": "Unknown",
        "email": None,
        "phone": None,
        "skills": [],
        "experience": [],
        "education": [],
        "summary": text[:2500] + "..." if len(text) > 2500 else text,  # Increased to 2500
        "location": None,
        "certifications": [],
        "projects": []
    }
    
    # Extract emails using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        parsed_data["email"] = emails[0]
    
    # Extract phone numbers using improved regex patterns
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\d{10}',  # +91-9876543210 or 9876543210
        r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +91-987-654-3210
        r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',  # (987) 654-3210
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 987-654-3210
        r'\+\d{12}',  # +919876543210
        r'\d{10}'  # 9876543210
    ]
    
    phones = []
    for pattern in phone_patterns:
        found_phones = re.findall(pattern, text)
        phones.extend(found_phones)
    
    if phones:
        # Clean and format the first found phone number
        phone = phones[0]
        if isinstance(phone, tuple):
            phone = ''.join(phone)
        # Remove extra spaces and format nicely
        phone = re.sub(r'[-.\s]+', '-', phone.strip())
        parsed_data["phone"] = phone
    
    # Extract person names using multiple approaches
    names = []
    
    # Method 1: spaCy NER (filter out technology names)
    spacy_names = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Filter out common technology names that might be misclassified
            tech_names = ['react', 'angular', 'vue', 'python', 'java', 'javascript', 'bootstrap', 'node', 'django', 'flask']
            if ent.text.lower() not in tech_names:
                spacy_names.append(ent.text)
    names.extend(spacy_names)
    
    # Method 2: Look for patterns at the beginning of the resume
    lines = text.strip().split('\n')
    for i, line in enumerate(lines[:5]):  # Check first 5 lines
        line = line.strip()
        # Skip common headers and technology names
        if any(header in line.lower() for header in ['resume', 'cv', 'curriculum', 'vitae']):
            continue
        
        # Skip lines that are clearly technology names
        tech_indicators = ['react', 'angular', 'vue', 'python', 'java', 'javascript', 'bootstrap', 'node', 'django', 'flask', 'framework', 'library', 'technology']
        if any(tech in line.lower() for tech in tech_indicators):
            continue
            
        # Look for name patterns (2-4 words, proper case)
        words = line.split()
        if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word.isalpha()):
            # Check if it looks like a name (no numbers, common punctuation, no tech terms)
            if not any(char.isdigit() for char in line) and not any(char in line for char in ['@', ':', '|', 'www']):
                # Additional check: ensure it doesn't contain common tech terms
                line_lower = line.lower()
                if not any(tech in line_lower for tech in tech_indicators):
                    names.append(line)
    
    # Method 3: Pattern matching for Indian names (with tech filtering)
    name_patterns = [
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$',  # First Last or First Middle Last
        r'^([A-Z][A-Z\s]+)\s*$'  # ALL CAPS names
    ]
    
    for line in lines[:3]:
        for pattern in name_patterns:
            match = re.match(pattern, line.strip())
            if match:
                candidate_name = match.group(1)
                # Filter out technology names
                tech_indicators = ['react', 'angular', 'vue', 'python', 'java', 'javascript', 'bootstrap', 'node', 'django', 'flask']
                if not any(tech in candidate_name.lower() for tech in tech_indicators):
                    names.append(candidate_name)
    
    # Method 4: Look for email patterns to extract name from email
    if parsed_data.get("email"):
        email = parsed_data["email"]
        # Extract name from email (before @ symbol)
        email_name = email.split('@')[0]
        # Clean up email name (remove numbers, dots, underscores)
        clean_name = re.sub(r'[0-9._-]', ' ', email_name)
        clean_name = ' '.join(word.capitalize() for word in clean_name.split() if len(word) > 1)
        if clean_name and len(clean_name.split()) >= 2:
            names.append(clean_name)
    
    if names:
        # Use the first reasonable name found
        parsed_data["name"] = names[0]
    else:
        # Fallback: try to extract from filename or use "Unknown"
        parsed_data["name"] = "Unknown Candidate"
    
    # Enhanced skills extraction with comprehensive keywords
    skill_keywords = [
        # Frontend Technologies
        "html", "html5", "css", "css3", "javascript", "typescript", "jsx", "tsx",
        "react", "react.js", "reactjs", "redux", "redux toolkit", "mobx", "context api",
        "angular", "angularjs", "vue", "vue.js", "vuejs", "nuxt", "nuxt.js",
        "svelte", "ember", "backbone", "jquery", "bootstrap", "tailwind", "tailwind css",
        "material ui", "material-ui", "mui", "ant design", "chakra ui", "semantic ui",
        "sass", "scss", "less", "stylus", "postcss", "webpack", "vite", "parcel",
        "rollup", "babel", "eslint", "prettier", "jest", "cypress", "selenium",
        
        # Backend Technologies  
        "node.js", "nodejs", "express", "express.js", "fastapi", "django", "flask",
        "python", "java", "c#", "c++", "php", "ruby", "go", "rust", "kotlin", "swift",
        "spring", "spring boot", "laravel", "symfony", "rails", "ruby on rails",
        
        # Databases
        "mongodb", "mysql", "postgresql", "sqlite", "redis", "elasticsearch",
        "cassandra", "dynamodb", "firebase", "firestore", "couchdb", "neo4j",
        
        # Cloud & DevOps
        "aws", "amazon web services", "azure", "google cloud", "gcp", "heroku",
        "netlify", "vercel", "docker", "kubernetes", "jenkins", "gitlab ci", "github actions",
        "terraform", "ansible", "nginx", "apache", "linux", "ubuntu", "centos",
        
        # Mobile Development
        "react native", "flutter", "ionic", "xamarin", "android", "ios", "swift", "kotlin",
        
        # Data & Analytics
        "machine learning", "ai", "artificial intelligence", "data science", "pandas",
        "numpy", "tensorflow", "pytorch", "scikit-learn", "jupyter", "matplotlib",
        "tableau", "power bi", "excel", "sql", "nosql",
        
        # Design & UI/UX
        "figma", "sketch", "adobe xd", "photoshop", "illustrator", "ui design", "ux design",
        "wireframing", "prototyping", "user research", "usability testing",
        
        # Version Control & Tools
        "git", "github", "gitlab", "bitbucket", "svn", "jira", "confluence", "slack",
        "trello", "asana", "notion", "visual studio code", "vscode", "intellij", "webstorm",
        
        # API & Integration
        "rest api", "restful", "graphql", "soap", "microservices", "json", "xml",
        "postman", "insomnia", "swagger", "openapi",
        
        # Testing
        "unit testing", "integration testing", "tdd", "bdd", "mocha", "chai", "jasmine",
        "karma", "protractor", "testng", "junit", "pytest", "cucumber"
    ]
    
    # Extract skills using multiple methods
    found_skills = set()
    text_lower = text.lower()
    
    # Method 1: Direct keyword matching
    for skill in skill_keywords:
        if skill in text_lower:
            found_skills.add(skill.title())
    
    # Method 2: Look for skills section
    lines = text.split('\n')
    skills_section_found = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in ['skills', 'technical skills', 'technologies', 'tools', 'programming languages']):
            skills_section_found = True
            
            # Extract skills from the next few lines
            for j in range(i+1, min(i+10, len(lines))):
                skills_line = lines[j].strip()
                if not skills_line or any(section in skills_line.lower() for section in ['experience', 'education', 'projects', 'certifications']):
                    break
                    
                # Split by common delimiters and extract potential skills
                delimiters = [',', '|', '•', '-', '/', '\\', ';', '&', 'and']
                potential_skills = [skills_line]
                
                for delimiter in delimiters:
                    new_skills = []
                    for skill in potential_skills:
                        new_skills.extend([s.strip() for s in skill.split(delimiter)])
                    potential_skills = new_skills
                
                # Add skills that match our keywords or look technical
                for potential_skill in potential_skills:
                    clean_skill = potential_skill.strip().lower()
                    if len(clean_skill) > 1:
                        # Check if it matches our known skills
                        for known_skill in skill_keywords:
                            if known_skill in clean_skill or clean_skill in known_skill:
                                found_skills.add(potential_skill.strip().title())
                                break
                        
                        # Add if it looks like a technical skill (contains common patterns)
                        if any(pattern in clean_skill for pattern in ['.js', '.py', '.java', 'script', 'framework', 'library']):
                            found_skills.add(potential_skill.strip().title())
            break
    
    # Method 3: Extract programming languages and frameworks from context
    programming_patterns = [
        r'\b(python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust|kotlin|swift)\b',
        r'\b(react|angular|vue|django|flask|spring|laravel|rails)\b',
        r'\b(html5?|css3?|sass|scss|less)\b',
        r'\b(aws|azure|docker|kubernetes|git|mongodb|mysql|postgresql)\b'
    ]
    
    for pattern in programming_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            found_skills.add(match.title())
    
    # Keep all extracted skills (no hard limit)
    parsed_data["skills"] = list(found_skills)
    
    # Extract education (basic pattern matching)
    education_patterns = [
        r'(bachelor|master|phd|b\.tech|m\.tech|bca|mca|b\.sc|m\.sc)\s+.*?(?:\n|$)',
        r'(university|college|institute)\s+.*?(?:\n|$)'
    ]
    
    education = []
    for pattern in education_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        education.extend(matches)
    
    parsed_data["education"] = education[:3]  # Limit to 3 entries
    
    # Enhanced work experience extraction
    experience = []
    lines = text.split('\n')
    
    # Job title patterns for better recognition
    job_title_patterns = [
        r'(senior|lead|principal|junior)?\s*(software|web|frontend|backend|full[\s-]?stack|ui/ux|react|angular|vue)?\s*(engineer|developer|programmer|designer|architect|analyst|consultant|manager|intern|specialist)',
        r'(technical|project|product|engineering|development)\s+(manager|lead|director)',
        r'(ui|ux|product|graphic|web)\s+designer',
        r'(data|business|systems?)\s+analyst',
        r'(devops|qa|test|quality\s+assurance)\s+(engineer|analyst|specialist)'
    ]
    
    # Date patterns for work timeline
    date_patterns = [
        r'(\d{1,2}[/-]\d{4}\s*[-–—to]\s*\d{1,2}[/-]\d{4})',  # MM/YYYY - MM/YYYY
        r'(\d{4}\s*[-–—to]\s*\d{4})',                          # YYYY - YYYY
        r'(\d{4}\s*[-–—to]\s*present)',                        # YYYY - Present
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}\s*[-–—to]\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}',  # Month YYYY - Month YYYY
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}\s*[-–—to]\s*present'  # Month YYYY - Present
    ]
    
    # Look for experience section
    experience_section_found = False
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in ['experience', 'employment', 'work history', 'career', 'professional experience']):
            experience_section_found = True
            
            # Extract structured experience entries
            j = i + 1
            current_experience = {}
            
            while j < len(lines) and j < i + 20:  # Look ahead max 20 lines
                exp_line = lines[j].strip()
                
                if not exp_line:
                    j += 1
                    continue
                
                # Check if this line contains a job title
                is_job_title = any(re.search(pattern, exp_line, re.IGNORECASE) for pattern in job_title_patterns)
                
                # Check if this line contains dates
                has_dates = any(re.search(pattern, exp_line, re.IGNORECASE) for pattern in date_patterns)
                
                # If we find a new job title or reached another section, save current experience
                if (is_job_title or exp_line.lower() in ['education', 'skills', 'projects', 'certifications']) and current_experience:
                    experience.append(current_experience)
                    current_experience = {}
                
                if is_job_title:
                    current_experience['title'] = exp_line
                elif has_dates:
                    current_experience['duration'] = exp_line
                    # Try to extract company name from the same line or previous line
                    if 'company' not in current_experience and j > 0:
                        prev_line = lines[j-1].strip()
                        # Company is often on the line before dates or in the same line
                        company_part = exp_line.split('-')[0].strip() if '-' in exp_line else prev_line
                        if company_part and not any(re.search(pattern, company_part, re.IGNORECASE) for pattern in date_patterns):
                            current_experience['company'] = company_part
                elif len(exp_line) > 20 and '•' in exp_line or exp_line.startswith('-'):
                    # This looks like a responsibility/description
                    if 'description' not in current_experience:
                        current_experience['description'] = exp_line
                elif len(exp_line) > 5 and 'company' not in current_experience and not has_dates:
                    # Might be a company name
                    current_experience['company'] = exp_line
                
                j += 1
            
            # Add the last experience entry
            if current_experience:
                experience.append(current_experience)
            break
    
    # If no structured experience section found, try pattern matching
    if not experience_section_found:
        for line in lines:
            # Look for lines that contain job titles and dates together
            for job_pattern in job_title_patterns:
                job_match = re.search(job_pattern, line, re.IGNORECASE)
                if job_match:
                    for date_pattern in date_patterns:
                        date_match = re.search(date_pattern, line, re.IGNORECASE)
                        if date_match:
                            experience.append({
                                'title': job_match.group(0),
                                'duration': date_match.group(0),
                                'description': line
                            })
                            break
    
    # Fallback: if still no experience, extract any line with job titles
    if not experience:
        for line in lines:
            for pattern in job_title_patterns:
                if re.search(pattern, line, re.IGNORECASE) and len(line.strip()) > 5:
                    experience.append(line.strip())
                    if len(experience) >= 5:
                        break
    
    parsed_data["experience"] = experience[:5]  # Limit to 5 entries
    
    return parsed_data


async def parse_resume_text(text: str) -> Dict[Any, Any]:
    """Parse resume text using spaCy NLP (no AI dependency)"""
    # Use spaCy parsing directly (no Gemini AI)
    print("Using spaCy NLP parsing...")
    return _parse_with_spacy_text(text)
