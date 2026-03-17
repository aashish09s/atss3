# 🔍 Current Parsing & Matching System - Technical Details

## 📋 Overview (सारांश)

Yeh document explain karta hai ki **abhi currently** project mein parsing aur matching ke liye **kya use ho raha hai**.

---

## 🧠 Resume Parsing (Resume निकालने के लिए)

### **Primary Method: NER (Named Entity Recognition) Model**

**Currently Active**: ✅ **Hugging Face NER Model**

#### 1. **Main NER Model** (Primary)
- **Model Name**: `yashpwr/resume-ner-bert-v2`
- **Type**: Resume-specific BERT model
- **Accuracy**: 90.87% F1 score
- **Entity Types**: 25 types (Name, Email, Phone, Companies, Designation, Skills, Experience, Education, etc.)
- **Location**: `backend/app/services/ner_resume_service.py`
- **Status**: ✅ **Currently Active**

#### 2. **Fallback NER Model** (If main fails)
- **Model Name**: `dslim/bert-base-NER`
- **Type**: Generic BERT NER model
- **Status**: Backup option

#### 3. **spaCy NLP** (Supporting)
- **Model**: `en_core_web_sm`
- **Usage**: 
  - Experience extraction
  - Education extraction
  - Name extraction (fallback)
- **Location**: Used in `ner_resume_service.py` and `parse_store.py`
- **Status**: ✅ **Active as supporting tool**

### **Secondary Method: Rule-based Parsing**

**Location**: `backend/app/services/parse_store.py`

- **Regex Patterns**: Email, phone, name extraction
- **Text Preprocessing**: Handles PDF formatting issues
- **Basic Parsing**: Fast duplicate checking
- **Status**: ✅ **Active for basic extraction**

### **NOT Currently Used** ❌

1. **Gemini AI** - ❌ Disabled (commented out in `ai_parse.py`)
2. **Ollama** - ❌ Not used for parsing (only for matching)
3. **OpenAI/Claude** - ❌ Not integrated

---

## 🎯 Resume Matching / ATS Scoring (Matching के लिए)

### **Primary Method: Hybrid Approach**

**Location**: `backend/app/services/ai_service.py` → `score_resume_against_jd()`

#### **Fallback Chain (Priority Order)**:

1. **Ollama AI** (Optional - if enabled)
   - **Model**: `deepseek-r1:8b` (local model)
   - **Status**: ⚠️ **Optional** - Only if `OLLAMA_ENABLED=true` in `.env`
   - **Timeout**: 15 seconds (very short)
   - **Usage**: Tries first, but falls back quickly if timeout

2. **Enhanced Fallback** (PRIMARY METHOD) ✅
   - **Algorithm**: Hybrid similarity + skill matching
   - **Components**:
     - **TF-IDF Vectorization**: Text similarity
     - **Sentence Transformers**: `all-MiniLM-L6-v2` (semantic similarity)
     - **Skill Matching**: Comprehensive tech skills database
     - **Experience Matching**: Years of experience comparison
   - **Status**: ✅ **Currently Active as Primary Method**

3. **NER-based Scoring** (Alternative)
   - **Location**: `backend/app/services/ner_resume_service.py`
   - **Function**: `score_resume_with_ner_optimized()`
   - **Method**: 
     - Uses NER-extracted entities
     - Cosine similarity calculation
     - Skill matching with Jaccard similarity
   - **Status**: ✅ **Available but not primary**

### **Matching Algorithms Used**:

1. **TF-IDF Cosine Similarity**
   - Text-based similarity
   - Uses sklearn's TfidfVectorizer

2. **Sentence Transformers**
   - Model: `all-MiniLM-L6-v2`
   - Semantic similarity
   - Better understanding of context

3. **Skill Matching**
   - Jaccard similarity (70%)
   - TF-IDF cosine on skills (30%)
   - Comprehensive tech skills database (200+ skills)

4. **Experience Matching**
   - Compares resume experience vs JD requirement
   - Full credit if resume >= JD requirement
   - Partial credit if less

### **NOT Currently Used** ❌

1. **Gemini AI for Scoring** - ❌ Not primary (optional in some routes)
2. **OpenAI GPT** - ❌ Not integrated
3. **Claude** - ❌ Not integrated

---

## 📊 Current System Architecture

```
Resume Upload
    ↓
Text Extraction (pdfplumber, python-docx)
    ↓
┌─────────────────────────────────────┐
│  PARSING LAYER                       │
├─────────────────────────────────────┤
│  ✅ NER Model (yashpwr/resume-ner)  │
│  ✅ spaCy NLP (supporting)           │
│  ✅ Regex patterns (basic info)     │
└─────────────────────────────────────┘
    ↓
Structured Data (name, email, skills, experience)
    ↓
┌─────────────────────────────────────┐
│  MATCHING/SCORING LAYER             │
├─────────────────────────────────────┤
│  1. Try Ollama (if enabled)         │
│  2. Enhanced Fallback (PRIMARY) ✅   │
│     - TF-IDF + Sentence Transformers│
│     - Skill matching                 │
│     - Experience matching            │
│  3. NER-based scoring (alternative) │
└─────────────────────────────────────┘
    ↓
ATS Score (0-100) + Analysis
```

---

## 🔧 Configuration Files

### **Environment Variables** (`.env`)

```bash
# Ollama (Optional - for matching only)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=deepseek-r1:8b
OLLAMA_ENABLED=false  # Usually disabled

# Gemini (NOT USED for parsing/matching)
GEMINI_API_KEY=your_key_here  # Not actively used

# spaCy (Required)
# Model downloaded via: python -m spacy download en_core_web_sm
```

---

## 📝 Code Locations

### **Parsing Services**:
1. **Main NER Service**: `backend/app/services/ner_resume_service.py`
   - `extract_entities_with_ner()` - Main parsing function
   - `_get_ner_model()` - Loads Hugging Face model

2. **Basic Parsing**: `backend/app/services/parse_store.py`
   - `parse_resume_text_basic()` - Fast basic parsing
   - `parse_and_store()` - Full parsing with storage

3. **Legacy Parser**: `backend/app/services/ai_parse.py`
   - `parse_resume_text()` - Uses spaCy only (Gemini disabled)

### **Matching/Scoring Services**:
1. **Main Scoring**: `backend/app/services/ai_service.py`
   - `score_resume_against_jd()` - Primary scoring function
   - `score_resume_with_ollama()` - Ollama integration (optional)

2. **NER-based Scoring**: `backend/app/services/ner_resume_service.py`
   - `score_resume_with_ner_optimized()` - Alternative scoring

3. **Resume Matching**: `backend/app/services/resume_matching/`
   - `resume_analysis.py` - Hybrid similarity approach
   - `matcher.py` - Filtering and matching logic

---

## 🎯 Summary (सारांश)

### **Parsing के लिए**:
- ✅ **Primary**: Hugging Face NER Model (`yashpwr/resume-ner-bert-v2`)
- ✅ **Supporting**: spaCy NLP + Regex patterns
- ❌ **NOT Used**: Gemini AI, Ollama (for parsing)

### **Matching के लिए**:
- ✅ **Primary**: Enhanced Fallback (TF-IDF + Sentence Transformers + Skill Matching)
- ⚠️ **Optional**: Ollama AI (if enabled)
- ✅ **Alternative**: NER-based scoring
- ❌ **NOT Used**: Gemini AI (as primary), OpenAI, Claude

---

## 🚀 Performance

- **Parsing Speed**: Fast (NER model is optimized)
- **Matching Speed**: Very fast (local models, no API calls)
- **Accuracy**: 
  - Parsing: ~90% (NER model F1 score)
  - Matching: Good (hybrid approach with multiple signals)

---

## ⚙️ Dependencies

### **Required**:
- `transformers` (Hugging Face)
- `torch` (PyTorch)
- `spacy` + `en_core_web_sm` model
- `sentence-transformers`
- `scikit-learn` (TF-IDF)

### **Optional**:
- `ollama` (for Ollama integration)
- `faiss` (for vector search - not currently used)

---

**Last Updated**: Based on current codebase analysis
**Status**: ✅ Production-ready, using local models (no external API dependencies for core features)


