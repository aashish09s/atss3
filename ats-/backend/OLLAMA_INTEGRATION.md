# Ollama Integration for AI Service

This document explains the Ollama integration added to the AI service as a fallback method for resume parsing and scoring.

## Overview

The Ollama integration provides a local AI model fallback when Gemini AI is unavailable or fails. It uses the `deepseek-r1:8b` model running locally via Ollama.

## Fallback Chain

The AI service now follows this fallback chain:

1. **Gemini AI** (Primary) - Google's cloud-based AI service
2. **Ollama Local Model** (Secondary) - Local `deepseek-r1:8b` model
3. **Heuristic Parsing** (Final) - Rule-based parsing with spaCy and regex

## Configuration

Add these settings to your `.env` file:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=deepseek-r1:8b
OLLAMA_ENABLED=true
```

## Setup Instructions

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai/](https://ollama.ai/)

### 2. Pull the Model

```bash
ollama pull deepseek-r1:8b
```

### 3. Start Ollama Server

```bash
ollama serve
```

### 4. Install Python Dependencies

```bash
# Install the Ollama client
pip install ollama==0.3.1

# Or run the setup script
python setup_ollama.py
```

## Testing

Run the test script to verify the integration:

```bash
python test_ollama_integration.py
```

## Features

### Job Description Parsing

The Ollama integration can parse job descriptions and extract:
- Job title
- Requirements
- Technical skills
- Experience level
- Responsibilities
- Location, salary, education, industry

### Resume Scoring

The Ollama integration can score resumes against job descriptions and provide:
- Overall match score (0-100)
- Detailed reasons for the score
- Missing skills analysis
- Candidate strengths
- Experience alignment assessment
- Skill match percentage

## Error Handling

The integration includes comprehensive error handling:
- Graceful fallback when Ollama is unavailable
- JSON parsing error recovery
- Connection timeout handling
- Model availability checking

## Performance

- **Temperature**: 0.1 (low for consistent output)
- **Top-p**: 0.9
- **Max tokens**: 2000
- **Async execution**: Non-blocking API calls

## Troubleshooting

### Common Issues

1. **Ollama server not running**
   ```bash
   ollama serve
   ```

2. **Model not found**
   ```bash
   ollama pull deepseek-r1:8b
   ```

3. **Connection refused**
   - Check if Ollama is running on port 11434
   - Verify firewall settings

4. **JSON parsing errors**
   - The system automatically retries with regex extraction
   - Falls back to heuristic parsing if needed

### Logs

Check the application logs for Ollama-related messages:
- `"Gemini failed, trying Ollama..."`
- `"Ollama API error: ..."`
- `"Ollama failed, using enhanced fallback scoring..."`

## Benefits

1. **Privacy**: Local processing keeps data on-premises
2. **Reliability**: Reduces dependency on external APIs
3. **Cost**: No API usage fees for local models
4. **Speed**: Local processing can be faster than cloud APIs
5. **Offline**: Works without internet connection

## Future Enhancements

- Support for multiple Ollama models
- Model switching based on task type
- Performance optimization
- Batch processing capabilities
