# Resume Matching System Integration

## Overview
The resume matching system has been successfully integrated into the backend, providing AI-powered resume analysis and matching capabilities.

## What Was Integrated

### 1. Core Modules
- **Models** (`app/services/resume_matching/models.py`): Data models for resumes, job descriptions, and matching results
- **Parser** (`app/services/resume_matching/parser.py`): Resume parsing using NLP and regex patterns
- **Embedding Store** (`app/services/resume_matching/embedding_store.py`): Vector embeddings using sentence-transformers and FAISS
- **Matcher** (`app/services/resume_matching/matcher.py`): Resume matching engine with similarity search and filtering
- **JD Processor** (`app/services/resume_matching/jd_processor.py`): Job description processing and skill extraction
- **Gemini Suggestions** (`app/services/resume_matching/gemini_suggestions.py`): AI-powered analysis using Google Gemini
- **Orchestrator** (`app/services/resume_matching/orchestrator.py`): Main workflow coordinator

### 2. API Endpoints
All endpoints are available under `/api/hr/resume-matching/`:

- **POST** `/process-resumes` - Process multiple resume files for AI matching
- **GET** `/processing-status/{job_id}` - Get status of resume processing job
- **POST** `/process-job-description` - Process a job description for matching
- **POST** `/find-matches/{jd_id}` - Find resumes matching a job description
- **POST** `/complete-workflow` - Complete workflow: process resumes and find matches
- **POST** `/analyze-single-resume` - Analyze a single resume against a job description
- **GET** `/system-stats` - Get system statistics
- **GET** `/resume/{resume_id}` - Get details of a processed resume
- **GET** `/job-description/{jd_id}` - Get details of a processed job description

### 3. Configuration
Added resume matching settings to `app/core/config.py`:
- `resume_matching_gemini_model`: Gemini model to use
- `resume_matching_faiss_index_path`: Path for FAISS index storage
- `resume_matching_embeddings_model`: Sentence transformer model
- `resume_matching_max_workers`: Maximum workers for processing
- `resume_matching_batch_size`: Batch size for processing
- `resume_matching_max_resumes_for_gpt`: Max resumes for GPT analysis
- `resume_matching_similarity_threshold`: Similarity threshold for matching
- `resume_matching_upload_dir`: Upload directory
- `resume_matching_processed_dir`: Processed files directory
- `resume_matching_logs_dir`: Logs directory

### 4. Dependencies
Added to `requirements.txt`:
- `sentence-transformers==2.2.2` - For generating embeddings
- `faiss-cpu==1.7.4` - For vector similarity search
- `pdfplumber==0.10.3` - For PDF text extraction

## Features

### Resume Processing
- Supports PDF and DOCX files
- Extracts structured data (name, email, phone, skills, experience)
- Uses spaCy NLP for advanced text processing
- Bulk processing with multiprocessing support

### Job Description Processing
- Extracts required and preferred skills
- Identifies experience requirements
- Processes job titles and company names
- Generates embeddings for similarity matching

### AI-Powered Matching
- Vector similarity search using FAISS
- Skills-based filtering
- Experience level matching
- Gemini AI analysis for detailed insights

### Analysis Features
- Match percentage scoring
- Missing skills identification
- Strengths analysis
- Improvement suggestions
- Interview questions generation
- Hire/Maybe/No recommendations

## Usage Examples

### 1. Process Resumes
```bash
curl -X POST "http://localhost:8000/api/hr/resume-matching/process-resumes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"
```

### 2. Process Job Description
```bash
curl -X POST "http://localhost:8000/api/hr/resume-matching/process-job-description" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Senior Python Developer...",
    "title": "Senior Python Developer",
    "company": "Tech Company Inc."
  }'
```

### 3. Find Matches
```bash
curl -X POST "http://localhost:8000/api/hr/resume-matching/find-matches/JD_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "top_k": 100,
    "similarity_threshold": 0.7,
    "enable_gpt_analysis": true
  }'
```

### 4. Complete Workflow
```bash
curl -X POST "http://localhost:8000/api/hr/resume-matching/complete-workflow" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx" \
  -F "job_description=We are looking for a Senior Python Developer..." \
  -F "job_title=Senior Python Developer" \
  -F "company=Tech Company Inc."
```

## Environment Variables
Make sure to set these in your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Testing
Run the integration test:
```bash
cd backend
python test_resume_matching_integration.py
```

## Benefits of Integration

1. **Unified System**: Resume matching is now part of the main backend, not a separate service
2. **Shared Authentication**: Uses the same RBAC system as other endpoints
3. **Consistent API**: Follows the same patterns as other backend routes
4. **Shared Configuration**: Uses the main backend configuration system
5. **Better Performance**: No need for separate service communication
6. **Easier Deployment**: Single application to deploy and manage

## Next Steps

1. **Frontend Integration**: Update the frontend to use the new resume matching endpoints
2. **Database Integration**: Store processed resumes and job descriptions in MongoDB
3. **Caching**: Add Redis caching for frequently accessed data
4. **Monitoring**: Add metrics and monitoring for the resume matching system
5. **Testing**: Add comprehensive unit and integration tests

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Gemini API Errors**: Check your API key and quota
   ```bash
   export GEMINI_API_KEY=your_key_here
   ```

3. **FAISS Index Issues**: Delete the index files to rebuild
   ```bash
   rm -rf ./data/faiss_index.*
   ```

4. **Memory Issues**: Reduce batch size or max workers in configuration

### Logs
Check the logs in the configured logs directory for detailed error information.

## Support
For issues or questions, check the logs and ensure all dependencies are properly installed and configured.
