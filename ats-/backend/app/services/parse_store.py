import os
import re
from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from app.db.mongo import get_db
from app.utils.text_extraction import extract_text_from_file
import asyncio
from app.services.ollama_resume_parser import parse_resume_with_ollama


def deduplicate_skills(skills):
    import re
    from difflib import SequenceMatcher

    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    def normalize(s):
        # Remove brackets, lowercase, remove special chars
        s = re.sub(r'\s*\(.*?\)', '', str(s)).strip().lower()
        s = re.sub(r'[^a-z0-9\s]', '', s).strip()
        return s

    def is_abbrev_of(short, long):
        # Check if short is abbreviation of long
        # e.g. "ml" is abbrev of "machine learning"
        if len(short) > 5:
            return False
        words = long.split()
        initials = ''.join(w[0] for w in words if w)
        return short == initials

    cleaned = []
    seen = []

    for skill in skills:
        norm = normalize(skill)
        if not norm:
            continue

        is_duplicate = False
        for i, existing in enumerate(seen):
            if (
                norm == existing
                or norm in existing
                or existing in norm
                or similarity(norm, existing) > 0.82
                or is_abbrev_of(norm, existing)
                or is_abbrev_of(existing, norm)
            ):
                is_duplicate = True
                # Keep longer/fuller version
                if len(norm) > len(existing):
                    seen[i] = norm
                    # Update corresponding cleaned entry
                    for j, c in enumerate(cleaned):
                        if normalize(c) == existing:
                            cleaned[j] = skill
                            break
                break

        if not is_duplicate:
            seen.append(norm)
            cleaned.append(skill)

    return cleaned


def get_duplicate_check_fields(text_content: str) -> dict:
    """
    Minimal fields for duplicate check only: regex for email/phone, no full parsing.
    Does not run Ollama or heavy extraction; used only to get name/email/phone for duplicate detection.
    """
    try:
        email = extract_email_from_text(text_content or "")
        phone = extract_phone_from_text(text_content or "")
        # Name: use first non-empty line (max 60 chars) that is not email/phone, or empty
        name = ""
        for line in (text_content or "").splitlines():
            line = line.strip()
            if not line or len(line) > 60:
                continue
            if "@" in line or re.search(r"\d{10}", line):
                continue
            if re.match(r"^[A-Za-z\s\.\-']+$", line) and len(line) >= 2:
                name = line
                break
        return {"name": name or "", "email": email or "", "phone": phone or ""}
    except Exception:
        return {"name": "", "email": "", "phone": ""}


def _preprocess_text_for_extraction(text: str) -> str:
    """Preprocess text to improve extraction when PDF loses formatting"""
    try:
        # IMPORTANT: Don't break email addresses! Extract them first and protect them
        # Find all email addresses and replace with placeholder
        email_pattern = r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        emails = re.findall(email_pattern, text)
        email_placeholders = {}
        for i, email in enumerate(emails):
            placeholder = f"__EMAIL_{i}__"
            email_placeholders[placeholder] = email
            text = text.replace(email, placeholder, 1)  # Replace only first occurrence

        # Unicode/encoding normalization (generic)
        # - Replace NBSP and zero-width chars
        text = text.replace('\u00A0', ' ').replace('\u200b', '').replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')
        # - Remove PDF artifacts like (cid:NNN)
        text = re.sub(r'\(cid:\d+\)', ' ', text)
        # - Normalize fancy dashes to ASCII hyphen
        text = text.replace('\u2013', '-').replace('\u2014', '-')

        # Step 1: Add spaces around phone numbers (10+ digits)
        text = re.sub(r'(\d{10,})', r' \1 ', text)

        # Step 2: Add spaces between lowercase and uppercase (handles "yogeshN" -> "yogesh N")
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Step 3: Add spaces between uppercase and lowercase when followed by uppercase (handles "YOGESH.NBACHELOR" -> "YOGESH.N BACHELOR")
        text = re.sub(r'([A-Z]+\.?[A-Z])([A-Z][a-z])', r'\1 \2', text)

        # Step 4: Add spaces between letter and number (generic for both cases)
        text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)

        # Step 5: Add spaces between number and letter
        text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)

        # Step 6: Add spaces around dots followed by uppercase (handles "YOGESH.NBACHELOR" -> "YOGESH. N BACHELOR")
        text = re.sub(r'([A-Z]+)\.([A-Z])', r'\1. \2', text)

        # Step 7: Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Step 8: Restore email addresses
        for placeholder, email in email_placeholders.items():
            text = text.replace(placeholder, email)

        print(f"[PREPROCESS] After preprocessing (first 300 chars): {repr(text[:300])}")

        return text
    except Exception as e:
        print(f"[PREPROCESS] Error preprocessing text: {e}")
        import traceback
        traceback.print_exc()
        return text


def _clean_first_last(name: str) -> str:
    """Normalize to First Last only, dropping extra tokens like locations."""
    tokens = re.findall(r"[A-Za-z]+", name or "")
    if not tokens:
        return "Unknown"
    if len(tokens) == 1:
        return tokens[0].title()
    return f"{tokens[0].title()} {tokens[1].title()}"


def extract_name_from_text(text: str) -> str:
    """Extract candidate name from resume text using heuristic methods (no spaCy dependency)"""
    try:
        # Debug: Log text preview for name extraction
        text_preview = text[:300] if len(text) > 300 else text
        print(f"[NAME EXTRACT] Starting extraction. Text preview: {repr(text_preview)}")
        
        # Strategy 1: Look for full names in the first section (before email extraction)
        # Full names (3+ words) are more reliable than email-derived names
        full_name = _extract_full_name_from_top_section(text)
        if full_name:
            print(f"[NAME EXTRACT] [OK] Found full name at top: {full_name}")
            return full_name
        
        # Strategy 2: Try to extract from email (fallback)
        email_name = _extract_name_from_email(text)
        if email_name and _is_valid_name(email_name):
            print(f"[NAME EXTRACT] Found name from email: {email_name}")
            return email_name
        else:
            print(f"[NAME EXTRACT] Email extraction returned: '{email_name}' (not valid)")
        
        # Strategy 3: Look for name at the TOP of resume (most reliable position)
        # Names are almost always at the very top, before other sections
        # Get first 500 chars to be safe
        first_500 = text[:500]
        first_300 = text[:300]  # First 300 chars where name almost always is
        print(f"[NAME EXTRACT] Searching first 300 chars for top-of-resume name: {repr(first_300)}")
        
        # Pattern 1: Look for "YOGESH.N" or "YOGESH. N" pattern (common in resumes)
        # This is the most reliable - names are often ALL CAPS at the top
        top_name_patterns = [
            r'^([A-Z]{3,}\.[A-Z]{1,2})',  # YOGESH.N at start
            r'^([A-Z]{3,}\.\s+[A-Z]{1,2})',  # YOGESH. N at start
            r'^\s*([A-Z]{3,}\.[A-Z]{1,2})',  # YOGESH.N after whitespace
            r'([A-Z]{4,}\.[A-Z]{1,2})(?=\s|$|BACHELOR|EDUCATION|EXPERIENCE)',  # YOGESH.N before section headers
        ]
        
        for pattern in top_name_patterns:
            match = re.search(pattern, first_300, re.MULTILINE)
            if match:
                candidate = match.group(1).strip()
                print(f"[NAME EXTRACT] Found top-of-resume pattern match: '{candidate}'")
                # Skip if it's a section header
                if candidate.upper() not in ['CONTACT', 'SKILLS', 'LANGUAGES', 'HOBBIES', 'EDUCATION', 'EXPERIENCE', 'PROFILE', 'SUMMARY', 'OBJECTIVE']:
                    name = candidate.replace('.', ' ').strip()
                    name = ' '.join(word.capitalize() if word.isupper() else word for word in name.split())
                    if _is_valid_name(name):
                        print(f"[NAME EXTRACT] [OK] Found name at top of resume: {name}")
                        return name
        
        # Pattern 2: Look for all-caps words with dots in first section
        all_caps_dot_patterns = [
            r'\b([A-Z]{3,}\.?[A-Z]*)\b',  # YOGESH.N or YOGESH
            r'\b([A-Z]{3,}\.\s*[A-Z]{1,2})\b',  # YOGESH. N
            r'([A-Z]{3,}\.[A-Z]{1,2})',  # YOGESH.N (no word boundary)
        ]
        
        all_caps_matches = []
        for pattern in all_caps_dot_patterns:
            matches = re.findall(pattern, first_500)
            all_caps_matches.extend(matches)
        
        print(f"[NAME EXTRACT] All-caps matches: {all_caps_matches}")
        
        for match in all_caps_matches:
            # Skip if it's clearly not a name (too short, common words)
            if len(match) < 4:
                continue
            if any(skip in match for skip in ['EMAIL', 'PHONE', 'ADDRESS', 'RESUME', 'CV', 'CONTACT', 'LANGUAGES', 'SKILLS', 'HOBBIES', 'EDUCATION', 'BACHELOR', 'MASTER', 'PROFILE', 'SUMMARY']):
                continue
            # Convert to proper case
            name = match.replace('.', ' ').strip()
            name = ' '.join(word.capitalize() if word.isupper() else word for word in name.split())
            if _is_valid_name(name):
                print(f"[NAME EXTRACT] Found all-caps name: {name}")
                return name
        
        # Pattern 2: Look for name patterns like "yogesh.n" or "Yogesh N" in first section
        name_pattern_in_text = r'([A-Z][a-z]+\.?[a-z]*)\s+([A-Z][a-z]+\.?[a-z]*)'
        name_matches = re.findall(name_pattern_in_text, first_500)
        print(f"[NAME EXTRACT] Name pattern matches: {name_matches}")
        
        for match_tuple in name_matches:
            name = ' '.join(match_tuple).replace('.', ' ').strip()
            if _is_valid_name(name):
                print(f"[NAME EXTRACT] Found name from pattern: {name}")
                return name
        
        # Strategy 4: Aggressive regex patterns (handles edge cases like "yogesh.n", "YOGESH.N")
        print("[NAME EXTRACT] Trying aggressive regex...")
        regex_name = _extract_name_with_regex(text)
        if regex_name:
            return regex_name
        
        # Strategy 5: Look for all-caps names or names with dots in first section
        fallback_name = _extract_name_aggressive_fallback(text)
        if fallback_name:
            return fallback_name
        
        print("[NAME EXTRACT] No valid name found after all strategies")
        return ""
        
    except Exception as e:
        print(f"[NAME EXTRACT] Error in extraction: {e}, trying regex fallback...")
        return _extract_name_with_regex(text)


def _extract_full_name_from_top_section(text: str) -> str:
    """
    GENERIC name extraction: Works for ALL resume formats without pattern-specific logic.
    
    UNIVERSAL RULE: 
    1. Names appear in FIRST 1-2 LINES (100% of resumes)
    2. Names appear BEFORE contact info (phone/email/social) (100% of resumes)
    3. Names are 2-4 words, mostly alphabetic (95%+ of resumes)
    4. Names don't contain section headers, job titles, or tech terms
    
    Approach:
    1. Get first 2 lines
    2. Find first contact info (phone/email/social link)
    3. Extract text BEFORE contact info
    4. Find the longest valid name-like sequence (2-4 words)
    5. Validate it's not a section header or job title
    """
    try:
        # Step 1: Get first up to 8 lines (more permissive for resumes with name lower)
        lines = text.split('\n')[:8]
        first_line = lines[0].strip() if lines else ""
        second_line = lines[1].strip() if len(lines) > 1 else ""
        combined_text = (" ".join(l.strip() for l in lines if l)).strip()
        
        # Safely print first lines (handle Unicode characters)
        try:
            safe_first = first_line.encode('ascii', errors='replace').decode('ascii')
            safe_second = second_line.encode('ascii', errors='replace').decode('ascii')
            print(f"[NAME EXTRACT] First lines sample: {repr(safe_first)} | {repr(safe_second)}")
        except Exception:
            print(f"[NAME EXTRACT] First lines sample: [line1 length: {len(first_line)}, line2 length: {len(second_line)}]")
        
        # Step 2: Find first contact info marker (phone/email/social link)
        # These are UNIVERSAL markers that appear in 99%+ of resumes
        contact_markers = [
            r'\+?\d{10,}',  # Phone: +91 9354616027, 7026720645
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email: email@domain.com
            r'linkedin\.com|github\.com|twitter\.com|facebook\.com',  # Social links
            r'www\.',  # Website
            r'http[s]?://',  # URL
        ]
        
        contact_positions = []
        for marker_pattern in contact_markers:
            for match in re.finditer(marker_pattern, combined_text, re.IGNORECASE):
                contact_positions.append(match.start())
        
        # Step 3: Extract text BEFORE first contact info
        if contact_positions:
            first_contact_pos = min(contact_positions)
            text_before_contact = combined_text[:first_contact_pos].strip()
            print(f"[NAME EXTRACT] Text before contact info: {repr(text_before_contact)}")
        else:
            # No contact info found - use first line only
            text_before_contact = first_line.strip()
            print(f"[NAME EXTRACT] No contact info found, using first line: {repr(text_before_contact)}")
        
        # Step 4: Remove common prefixes that appear before names
        # These are NOT the name itself, but prefixes like "CONTACT", "Name:", etc.
        prefixes_to_remove = [
            r'^CONTACT\s+',
            r'^Contact\s+',
            r'^NAME:\s*',
            r'^Name:\s*',
            r'^Name\s+',
        ]
        
        for prefix_pattern in prefixes_to_remove:
            text_before_contact = re.sub(prefix_pattern, '', text_before_contact, flags=re.IGNORECASE).strip()
        
        # Step 5: Find valid name sequences (2-5 words)
        # Split into words and find sequences that look like names
        words = text_before_contact.split()
        
        # List of invalid words (section headers, job titles, tech terms)
        invalid_words = {
            'full', 'stack', 'developer', 'engineer', 'manager', 'director', 'lead', 'senior',
            'contact', 'email', 'phone', 'mobile', 'address', 'location',
            'resume', 'cv', 'curriculum', 'vitae',
            'profile', 'summary', 'objective',
            'education', 'experience', 'skills', 'languages', 'hobbies', 'projects',
            'bachelor', 'master', 'degree', 'diploma', 'certificate',
            'university', 'college', 'institute', 'school',
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node', 'django', 'flask',
        }
        
        # Try sequences of 5, 4, 3, and 2 words (longest first)
        best_name = None
        best_score = 0
        
        for length in [5, 4, 3, 2]:  # Try longer names first
            for i in range(len(words) - length + 1):
                candidate_words = words[i:i+length]
                candidate = ' '.join(candidate_words)
                
                # Skip if contains invalid words
                if any(word.lower() in invalid_words for word in candidate_words):
                    continue
                
                # Skip if contains numbers (not typical in names)
                if any(char.isdigit() for char in candidate):
                    continue
                
                # Skip if contains special chars (except hyphens/apostrophes for names like "Mary-Jane")
                if re.search(r'[^A-Za-z\s\-\']', candidate):
                    continue
                
                # Check if words look like name parts (mostly alphabetic, reasonable length)
                valid_words = []
                for word in candidate_words:
                    # Remove hyphens/apostrophes for validation
                    clean_word = word.replace('-', '').replace("'", '').replace('.', '')
                    if clean_word.isalpha() and 2 <= len(clean_word) <= 30:
                        valid_words.append(word)
                
                if len(valid_words) == length:
                    # Score based on:
                    # 1. Length (longer names are better)
                    # 2. Position (earlier is better)
                    # 3. Capitalization (all words capitalized is better)
                    score = length * 10  # Base score
                    score += (len(words) - i)  # Earlier position = higher score
                    
                    # Bonus for proper capitalization
                    if all(word[0].isupper() for word in valid_words):
                        score += 5
                    
                    if score > best_score:
                        best_score = score
                        best_name = ' '.join(valid_words)
                        print(f"[NAME EXTRACT] Candidate name (score {score}): {best_name}")
        
        # Step 6: Validate and format the best candidate
        if best_name:
            # Convert to proper case (Title Case)
            words_in_name = best_name.split()
            formatted_name = ' '.join(
                word.capitalize() if word.isupper() else word 
                for word in words_in_name
            )
            
            if _is_valid_name(formatted_name):
                print(f"[NAME EXTRACT] [OK] Found name (generic method): {formatted_name}")
                return formatted_name
        
        print(f"[NAME EXTRACT] No valid name found in first 8 lines")
        return ""
        
    except Exception as e:
        print(f"[NAME EXTRACT] Error in generic name extraction: {e}")
        import traceback
        traceback.print_exc()
        return ""


def _extract_name_from_email(text: str) -> str:
    """Extract name from email address (e.g., 'yogesh.n0070@gmail.com' -> 'Yogesh N')"""
    try:
        # More flexible email pattern - handles concatenated text
        # Look for @ followed by domain pattern
        email_pattern = r'([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+)\.([A-Z|a-z]{2,})'
        matches = re.findall(email_pattern, text)
        
        if matches:
            # Take the first email found
            email_local, domain, tld = matches[0]
            email_local_original = email_local
            email_local = email_local.lower()
            
            print(f"[NAME EXTRACT] Found email: {email_local}@{domain}.{tld}")
            
            # Problem: email might be concatenated like "languages7026720645yogesh.n0070"
            # Strategy: Look for the last valid name-like pattern before @
            
            # Try to find name patterns in the email local part
            # Pattern 1: Look for "name.n" or "name" before numbers
            # Extract everything before trailing digits
            name_before_numbers = re.sub(r'\d+$', '', email_local)
            print(f"[NAME EXTRACT] Email local after removing trailing numbers: {name_before_numbers}")
            
            # Pattern 2: Look for common name patterns (2-3 words, possibly with dots)
            # Try to find "yogesh.n" or "yogesh" pattern
            name_patterns = [
                r'([a-z]{3,}\.[a-z]{1,2})',  # "yogesh.n"
                r'([a-z]{4,})(?=\d|@)',  # "yogesh" followed by numbers or @
            ]
            
            best_name = None
            for pattern in name_patterns:
                matches_in_email = re.findall(pattern, email_local)
                print(f"[NAME EXTRACT] Pattern '{pattern}' found: {matches_in_email}")
                for match in matches_in_email:
                    # Check if it's a valid name (not common words)
                    if len(match) >= 4 and match.lower() not in ['email', 'gmail', 'yahoo', 'hotmail', 'outlook', 'contact', 'phone', 'languages', 'languages7026720645']:
                        # Prefer longer matches
                        if not best_name or len(match) > len(best_name):
                            best_name = match
            
            if best_name:
                print(f"[NAME EXTRACT] Found name in email: {best_name}")
                # Convert dots/underscores to spaces and capitalize
                name_part = best_name.replace('.', ' ').replace('_', ' ').replace('-', ' ')
                name_capitalized = ' '.join(word.capitalize() for word in name_part.split() if word)
                if len(name_capitalized.split()) >= 1:
                    print(f"[NAME EXTRACT] Final name from email: {name_capitalized}")
                    return name_capitalized
            
            # Fallback: Try original approach
            name_match = re.match(r'^([a-z]+(?:\.[a-z]+)?)', email_local)
            if name_match:
                name_part = name_match.group(1)
                # Skip if it's clearly not a name
                if name_part.lower() not in ['email', 'gmail', 'contact', 'languages']:
                    print(f"[NAME EXTRACT] Extracted name part from email: {name_part}")
                    
                    # Convert dots/underscores to spaces and capitalize
                    name_part = name_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
                    name_capitalized = ' '.join(word.capitalize() for word in name_part.split() if word)
                    if len(name_capitalized.split()) >= 1:
                        print(f"[NAME EXTRACT] Final name from email: {name_capitalized}")
                        return name_capitalized
            
            # If no match, try to clean the email local part
            # Remove trailing numbers
            cleaned = re.sub(r'\d+$', '', email_local)
            print(f"[NAME EXTRACT] Cleaned email local part: {cleaned}")
            
            # If it has dots, split and take parts
            if '.' in cleaned:
                parts = cleaned.split('.')
                print(f"[NAME EXTRACT] Email parts: {parts}")
                if len(parts) >= 1:
                    # Take first part(s) as name
                    name_parts = [p.capitalize() for p in parts[:2] if p and not p.isdigit() and len(p) >= 2]
                    if name_parts:
                        result = ' '.join(name_parts)
                        print(f"[NAME EXTRACT] Name from email parts: {result}")
                        return result
            
            # Last resort: just capitalize the first part before any numbers/dots
            first_part = re.split(r'[.\d_]', email_local)[0]
            if first_part and len(first_part) >= 2:
                result = first_part.capitalize()
                print(f"[NAME EXTRACT] Name from first part: {result}")
                return result
        
        print(f"[NAME EXTRACT] No email found in text")
        return ""
    except Exception as e:
        print(f"[NAME EXTRACT] Error extracting from email: {e}")
        import traceback
        traceback.print_exc()
        return ""


def _is_valid_name(name: str) -> bool:
    """Check if a name looks valid (not a false positive)"""
    if not name or len(name) < 2:
        return False
    
    words = name.split()
    if len(words) == 0:
        return False
    
    # Single word names are acceptable if they look like names
    if len(words) == 1:
        word = words[0]
        # Must be at least 3 characters
        if len(word) < 3:
            return False
        # Should be mostly letters (allow dots, hyphens, apostrophes)
        if not re.match(r'^[A-Za-z][A-Za-z0-9.\-\']*$', word):
            return False
        # Check if it's a common invalid word
        invalid_single = ['the', 'and', 'for', 'with', 'from', 'that', 'this', 'resume', 'cv', 'contact', 'email', 'phone']
        if word.lower() in invalid_single:
            return False
        return True
    
    # For multi-word names (2-4 words is typical for full names)
    if len(words) < 2 or len(words) > 4:
        return False
    
    # Filter out common false positives
    invalid_keywords = [
        'resume', 'cv', 'curriculum', 'vitae', 'profile', 'summary',
        'objective', 'experience', 'education', 'skills', 'projects',
        'email', 'phone', 'address', 'location', 'linkedin', 'github',
        'portfolio', 'website', 'www', 'http', 'https', 'com', 'net',
        'software', 'engineer', 'developer', 'manager', 'director'
    ]
    
    name_lower = name.lower()
    if any(keyword in name_lower for keyword in invalid_keywords):
        return False
    
    # Check capitalization - be more lenient for names
    # Allow all-caps names (like "YOGESH.N") or mixed case
    capital_count = sum(1 for word in words if word and (word[0].isupper() or word.isupper()))
    if capital_count < len(words) * 0.5:  # At least 50% should be capitalized (more lenient)
        return False
    
    # Check if name is too long (likely not a name)
    if len(name) > 50:
        return False
    
    # Check if name contains mostly letters and spaces (allow hyphens, apostrophes)
    if not re.match(r'^[A-Za-z\s\.\-\']+$', name):
        return False
    
    return True


def _extract_name_with_regex(text: str) -> str:
    """Fallback name extraction using regex patterns"""
    try:
        # Try multiple patterns for name extraction
        name_patterns = [
            # Pattern 1: Name at the very start of text (most common)
            # Handles: "John Doe", "YOGESH.N", "yogesh.n"
            r'^([A-Z][A-Za-z0-9.]+(?:\s+[A-Z][A-Za-z0-9.]+)*)',
            # Pattern 2: Name after "Name:" label
            r'(?:^|\n)Name[:\s]+([A-Z][A-Za-z0-9.]+(?:\s+[A-Z][A-Za-z0-9.]+)*)',
            # Pattern 3: Name after "Full Name:" label
            r'(?:^|\n)Full\s+Name[:\s]+([A-Z][A-Za-z0-9.]+(?:\s+[A-Z][A-Za-z0-9.]+)*)',
            # Pattern 4: Name after "Candidate:" label
            r'(?:^|\n)Candidate[:\s]+([A-Z][A-Za-z0-9.]+(?:\s+[A-Z][A-Za-z0-9.]+)*)',
            # Pattern 5: All-caps name on its own line (like "YOGESH.N")
            r'^([A-Z][A-Z0-9.]+(?:\s+[A-Z][A-Z0-9.]+)*)\s*\n',
            # Pattern 6: Name with dots (like "yogesh.n" or "YOGESH.N")
            r'^([A-Za-z]+\.[A-Za-z]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                candidate_name = match.group(1).strip()
                # Clean up the name
                candidate_name = candidate_name.strip('.,;:()[]{}')
                if _is_valid_name(candidate_name):
                    print(f"[NAME EXTRACT] Found name via regex: {candidate_name}")
                    return candidate_name
        
        # Pattern 7: Look in first 10 lines for name-like text (more aggressive)
        lines = text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            # Skip lines that are clearly not names
            if any(skip in line.lower() for skip in ['email', 'phone', 'address', 'resume', 'cv', 'summary', 'objective', 'experience', 'education']):
                continue
            
            # Check if line looks like a name
            if _is_valid_name(line):
                print(f"[NAME EXTRACT] Found name in first lines: {line}")
                return line
        
        print("[NAME EXTRACT] No valid name found with regex")
        return ""
        
    except Exception as e:
        print(f"[NAME EXTRACT] Error in regex extraction: {e}")
        return ""


def _extract_name_aggressive_fallback(text: str) -> str:
    """Aggressive fallback: Look for names in first section, including all-caps and with dots"""
    try:
        # Get first 500 characters (where name almost always appears)
        first_section = text[:500]
        
        # Look for all-caps words that might be names (like "YOGESH.N")
        # Pattern: 2-5 ALL CAPS words, possibly with dots
        all_caps_pattern = r'\b([A-Z][A-Z0-9.]+(?:\s+[A-Z][A-Z0-9.]+)*)\b'
        all_caps_matches = re.findall(all_caps_pattern, first_section)
        
        for match in all_caps_matches:
            # Skip if it's clearly not a name
            if len(match) < 3 or any(skip in match.lower() for skip in ['email', 'phone', 'address', 'resume', 'cv']):
                continue
            # Check if it looks like a name (2-5 words, contains letters)
            words = match.split()
            if 1 <= len(words) <= 5 and any(c.isalpha() for c in match):
                # Convert to proper case
                name = ' '.join(word.capitalize() if word.isupper() else word for word in words)
                if _is_valid_name(name):
                    print(f"[NAME EXTRACT] Found name via all-caps fallback: {name}")
                    return name
        
        # Look for names with dots (like "yogesh.n" or "YOGESH.N")
        dot_name_pattern = r'\b([A-Za-z]+\.[A-Za-z]+)\b'
        dot_matches = re.findall(dot_name_pattern, first_section)
        
        for match in dot_matches:
            # Skip if it's an email domain or URL
            if '@' in first_section or 'www' in first_section.lower():
                # Check position - if it's before @, it might be a name
                match_pos = first_section.find(match)
                at_pos = first_section.find('@')
                if at_pos > 0 and match_pos > at_pos:
                    continue  # Skip if it's after @ (likely part of email domain)
            
            # Convert to proper case
            name = ' '.join(word.capitalize() for word in match.split('.'))
            if _is_valid_name(name):
                print(f"[NAME EXTRACT] Found name with dot via fallback: {name}")
                return name
        
        return ""
        
    except Exception as e:
        print(f"[NAME EXTRACT] Error in aggressive fallback: {e}")
        return ""


def extract_email_from_text(text: str) -> str:
    """Extract email from resume text"""
    try:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    except:
        return ""


def extract_phone_from_text(text: str) -> str:
    """Extract phone number from resume text"""
    try:
        # Look for phone number patterns
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\d{10}\b',  # 10 digits
            r'\b\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'  # International
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    except:
        return ""


def _split_skills_into_individual(skills_block: dict) -> List[str]:
    """
    Take skills from Ollama (technical, soft, languages) and return a flat list
    where each item is ONE skill. Splits strings like "NumPy, Pandas, Matplotlib"
    or "Supervised & Unsupervised Learning" into separate skills.
    """
    if not isinstance(skills_block, dict):
        return []
    out = []
    for key in ("technical", "soft", "languages"):
        vals = skills_block.get(key)
        if not isinstance(vals, list):
            continue
        for v in vals:
            if not isinstance(v, str) or not v.strip():
                continue
            raw = v.strip()

            # Handle category style like "Data Analysis : Statistical Analysis, Data Preprocessing"
            # Keep the category itself as a skill too.
            if ":" in raw:
                left, right = raw.split(":", 1)
                left = left.strip()
                if left and len(left) < 60:
                    out.append(left)
                raw = right.strip()

            # Remove leading bullets / labels
            raw = re.sub(r"^[\-\•\*\u2022]+\s*", "", raw)

            # Split by comma, "&", "and", "/", "|" then strip each part
            parts = re.split(r"\s*,\s*|\s+&\s+|\s+and\s+|\s*/\s*|\s*\|\s*", raw)
            for p in parts:
                p = p.strip()
                if p and len(p) < 100:  # skip very long fragments
                    # Clean enclosing parentheses
                    p = p.strip("()[]{}").strip()
                    out.append(p)
    # Deduplicate preserving order
    seen = set()
    result = []
    for s in out:
        key = s.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result


def _augment_skills_with_text_signals(text: str, skills: List[str]) -> List[str]:
    """
    Some important conceptual skills (ML/DS/etc.) may appear only in summary/projects text.
    If they are present in the raw text but missing from skills, add them.
    """
    if not text:
        return skills

    text_lower = text.lower()
    existing = {s.lower() for s in skills}

    # Important multi-word concepts to ensure are present
    key_concepts = {
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "data analysis": "Data Analysis",
        "data preprocessing": "Data Preprocessing",
        "feature engineering": "Feature Engineering",
        "exploratory data analysis": "Exploratory Data Analysis (EDA)",
        "eda": "Exploratory Data Analysis (EDA)",
        "data visualization": "Data Visualization",
        "statistical analysis": "Statistical Analysis",
        "predictive modeling": "Predictive Modeling",
        "model evaluation": "Model Evaluation",
        "time series": "Time Series Analysis",
        "natural language processing": "Natural Language Processing (NLP)",
        "nlp": "Natural Language Processing (NLP)",
        "computer vision": "Computer Vision",
        "etl": "ETL",
        "data cleaning": "Data Cleaning",
    }

    augmented = list(skills)
    for needle, pretty in key_concepts.items():
        if needle in text_lower:
            # Avoid duplicates by loose match in existing skills
            if not any(needle in s.lower() or s.lower() in needle for s in existing):
                augmented.append(pretty)
                existing.add(needle)

    return augmented


def _separate_projects_from_experience(experience: list) -> tuple[list, list]:
    """
    Ollama sometimes puts projects inside `experience`. Move such entries into `projects`.

    Heuristics:
    - If company is missing/empty AND title looks like a project name (System, Project, Prediction, etc.)
    - If title explicitly contains 'project'
    """
    if not isinstance(experience, list):
        return [], []

    project_keywords = [
        "project",
        "system",
        "prediction",
        "classifier",
        "recommender",
        "capstone",
        "thesis",
        "minor project",
        "major project",
        "internship project",
        "final year",
    ]

    # Words that usually indicate real job roles
    job_title_keywords = [
        "intern",
        "engineer",
        "developer",
        "analyst",
        "scientist",
        "manager",
        "consultant",
        "lead",
        "architect",
        "specialist",
        "associate",
        "trainee",
    ]

    # Company-like strings that actually mean "personal/academic project"
    projectish_companies = [
        "self",
        "personal",
        "college",
        "university",
        "institute",
        "school",
        "freelance",
        "github",
        "portfolio",
        "academic",
    ]

    exp_out = []
    projects_out = []

    for item in experience:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "") or "").strip()
        company = str(item.get("company", "") or "").strip()
        duration = str(item.get("duration", "") or "").strip()
        highlights = item.get("highlights") or []

        title_l = title.lower()
        company_l = company.lower()
        is_projectish_title = any(k in title_l for k in project_keywords)
        has_company = bool(company) and company_l not in {"n/a", "na", "none", "unknown"}
        is_job_like_title = any(k in title_l for k in job_title_keywords)
        is_projectish_company = any(word in company_l for word in projectish_companies)

        # Decide if this entry is really a project:
        # - title looks like a project AND
        #   * no real company, OR
        #   * company itself looks academic/personal, OR
        #   * title does NOT look like a job role
        if title and is_projectish_title and (
            (not has_company) or is_projectish_company or (not is_job_like_title)
        ):
            projects_out.append(
                {
                    "name": title,
                    "duration": duration,
                    "highlights": highlights if isinstance(highlights, list) else [],
                }
            )
            continue

        exp_out.append(
            {
                "title": title,
                "company": company,
                "duration": duration,
                "highlights": highlights if isinstance(highlights, list) else [],
            }
        )

    return exp_out, projects_out


def _extract_skills_from_section(text: str) -> List[str]:
    """
    If the resume has an explicit Skills section, capture lines under that header.
    """
    skills = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if re.search(r'\bskills?\b', ln, re.IGNORECASE):
            # collect next few lines until a blank or a new section-like header
            for nxt in lines[i+1:i+8]:
                n = nxt.strip()
                if not n:
                    break
                if re.search(r'^(experience|education|projects|summary|objective|profile)\b', n, re.IGNORECASE):
                    break
                parts = re.split(r'[;,]', n)
                for p in parts:
                    p = p.strip()
                    if p:
                        skills.append(p)
            break
    return skills


async def parse_and_store(file_path: str, uploaded_by: str, filename: str, file_url: str) -> str:
    """Parse resume and store in database"""
    try:
        print(f"Starting parse and store for: {filename}")
        print(f"File path: {file_path}")
        print(f"Uploaded by: {uploaded_by}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text from file (async operation)
        print(f"Extracting text from {filename}...")
        text_content = await extract_text_from_file(file_path)
        
        print(f"Text extracted, length: {len(text_content)} characters")
        
        if not text_content.strip():
            raise Exception("No text content found in file")

        # -----------------------------
        # PARSING PIPELINE: Ollama is the only parser (top and sole).
        # No preprocessing, no NER, no regex extraction before or after.
        # Main parsing task = Ollama only.
        # -----------------------------
        parsed_data = None
        experience_cache = None

        print("[PARSE STORE] Parsing with Ollama (single source of truth)...")
        try:
            ollama_data = parse_resume_with_ollama(text_content)
            if ollama_data:
                print("[PARSE STORE] Ollama parser succeeded, mapping to internal schema...")
                # Normalize keys to lowercase (model may return "Personal", "Name" etc.)
                _o = {str(k).lower(): v for k, v in ollama_data.items()}
                _p = _o.get("personal")
                personal = {str(k).lower(): v for k, v in (_p or {}).items()} if isinstance(_p, dict) else {}
                _s = _o.get("skills")
                skills_block = {str(k).lower(): v for k, v in (_s or {}).items()} if isinstance(_s, dict) else {}

                all_skills = _split_skills_into_individual(skills_block)
                all_skills = _augment_skills_with_text_signals(text_content, all_skills)
                all_skills = deduplicate_skills(all_skills)

                # NOTE: ner_resume_service is ONLY used by jd.py for JD-resume matching.
                # Experience extraction uses Ollama output directly.
                # DO NOT re-add build_experience_cache — it gives WRONG results.
                experience_cache = None

                # All parsed fields from Ollama only (no merge with regex/section extraction)
                exp = _o.get("experience") if isinstance(_o.get("experience"), list) else []
                edu = _o.get("education") if isinstance(_o.get("education"), list) else []
                # certs = _o.get("certifications") if isinstance(_o.get("certifications"), list) else []
                raw_certs = _o.get("certifications") if isinstance(_o.get("certifications"), list) else []
                certs = []
                for c in raw_certs:
                    if isinstance(c, dict):
                        name = str(c.get("name") or "").strip()
                        issuer = str(c.get("issuer") or "").strip()
                        if issuer and name.lower().startswith(issuer.lower()):
                            name = name[len(issuer):].lstrip(" —:-")
                        if issuer and name.lower().endswith(issuer.lower()):
                            name = name[:-len(issuer)].rstrip(" —:-,")
                        if name:
                            certs.append(name)
                    elif isinstance(c, str) and c.strip():
                        certs.append(c.strip())
                proj = _o.get("projects") if isinstance(_o.get("projects"), list) else []
                summary_text = _o.get("summary") if isinstance(_o.get("summary"), str) else None

                # Normalize/move project-like entries out of experience
                exp_clean, projects_from_exp = _separate_projects_from_experience(exp)
                # Normalize projects from model (if present)
                normalized_projects = []
                for p in proj:
                    if isinstance(p, dict):
                        name = str(p.get("name", "") or p.get("title", "") or "").strip()
                        dur = str(p.get("duration", "") or "").strip()
                        hl = p.get("highlights") if isinstance(p.get("highlights"), list) else []
                        if name:
                            normalized_projects.append({"name": name, "duration": dur, "highlights": hl})
                    elif isinstance(p, str) and p.strip():
                        normalized_projects.append({"name": p.strip(), "duration": "", "highlights": []})

                parsed_data = {
                    "name": (personal.get("name") or "").strip() or "Unknown",
                    "email": (personal.get("email") or "").strip() or None,
                    "phone": (personal.get("phone") or "").strip() or None,
                    "skills": all_skills,
                    "experience": exp_clean,
                    "education": edu,
                    "summary": summary_text or text_content[:100].strip(),
                    "location": (personal.get("location") or "").strip() or "",
                    "certifications": certs,
                    "projects": normalized_projects + projects_from_exp,
                    "years_experience": int(_o.get("years_experience") or 0),
                }
            else:
                print("[PARSE STORE] Ollama returned no data.")
        except Exception as e:
            print(f"[PARSE STORE] Ollama parsing failed: {e}")

        # If Ollama failed or returned nothing: lightweight fallback so at least name/email/phone show
        if parsed_data is None:
            fallback = get_duplicate_check_fields(text_content)
            parsed_data = {
                "name": fallback.get("name") or "Unknown",
                "email": fallback.get("email") or None,
                "phone": fallback.get("phone") or None,
                "skills": [],
                "experience": [],
                "education": [],
                "summary": text_content[:100] + "..." if len(text_content) > 4000 else text_content,
                "location": None,
                "certifications": [],
                "projects": [],
            }
            print("[PARSE STORE] Using fallback (name/email/phone from text); Ollama did not return data.")
        
        # Get database
        db = await get_db()
        
        # Create resume document
        resume_doc = {
            "filename": filename,
            "file_url": file_url,
            "uploaded_by": uploaded_by,
            "status": "submission",
            "parsed_data": {
                "name": parsed_data.get("name", "Unknown"),
                "email": parsed_data.get("email"),
                "phone": parsed_data.get("phone"),
                # Store all parsed skills so UI can display full list
                "skills": parsed_data.get("skills", []),
                # Keep small previews for experience/education to avoid very large documents
                "experience": parsed_data.get("experience", [])[:3],
                "education": parsed_data.get("education", [])[:2],
                "summary": parsed_data.get("summary", ""),
                "location": parsed_data.get("location", "")
            },
            "ats_score": None,
            "shared_with_manager": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert resume - check for duplicate first (race condition protection)
        print(f"Saving resume to database...")
        try:
            # Check if a resume with the same filename and uploaded_by already exists (within last 5 minutes)
            # This prevents duplicate processing if the same file is queued twice
            from datetime import timedelta
            recent_duplicate = await db.resumes.find_one({
                "filename": filename,
                "uploaded_by": uploaded_by,
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(minutes=5)}
            })
            
            if recent_duplicate:
                print(f"[PARSE STORE] Duplicate resume detected (same filename + user within 5 min): {filename}")
                print(f"[PARSE STORE] Skipping duplicate processing. Existing resume ID: {recent_duplicate['_id']}")
                # Clean up temp file
                if os.path.exists(file_path):
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                return str(recent_duplicate['_id'])
            
            resume_result = await db.resumes.insert_one(resume_doc)
            resume_id = str(resume_result.inserted_id)
            print(f"Resume saved with ID: {resume_id}")
        except Exception as e:
            print(f"Failed to save resume: {str(e)}")
            raise Exception(f"Failed to save resume: {str(e)}")
        
        # Create detailed parsed profile
        profile_doc = {
            "resume_id": resume_id,
            "candidate_name": parsed_data.get("name", "Unknown"),
            "email": parsed_data.get("email"),
            "phone": parsed_data.get("phone"),
            "skills": parsed_data.get("skills", []),
            "experience": parsed_data.get("experience", []),
            "work_experience": parsed_data.get("experience", []),  # Also store as work_experience for frontend
            "education": parsed_data.get("education", []),
            "summary": parsed_data.get("summary") or "",
            "location": parsed_data.get("location"),
            "certifications": parsed_data.get("certifications", []),
            "projects": parsed_data.get("projects", []),
            "years_experience": parsed_data.get("years_experience", 0),
            "raw_text": text_content,
            "experience_cache": None,
            "created_at": datetime.now(timezone.utc)
        }
        
        print(f"Profile document created: {profile_doc.get('candidate_name')} - {len(profile_doc.get('skills', []))} skills")
        
        # Insert parsed profile - check for duplicate to prevent race condition
        print(f"Saving parsed profile to database...")
        try:
            # Check if parsed profile already exists for this resume_id (race condition protection)
            existing_profile = await db.parsed_resumes.find_one({"resume_id": resume_id})
            if existing_profile:
                print(f"[PARSE STORE] Parsed profile already exists for resume_id {resume_id}, skipping duplicate insert")
            else:
                await db.parsed_resumes.insert_one(profile_doc)
                print(f"Parsed profile saved")
        except Exception as e:
            print(f"Failed to save parsed profile: {str(e)}")
            # Don't raise exception - resume is already saved, profile is secondary
            # Log error but continue
            import traceback
            traceback.print_exc()
        
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            print(f"Failed to clean up temp file: {e}")
        
        print(f"Parse and store completed successfully for {filename}")
        return resume_id
        
    except Exception as e:
        print(f"Error in parse_and_store for {filename}: {str(e)}")
        # Clean up temporary file on error
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"Cleaned up temp file after error: {file_path}")
        except Exception as cleanup_error:
            print(f"Failed to clean up temp file after error: {cleanup_error}")
        
        raise Exception(f"Failed to parse and store resume: {str(e)}")
