# Ollama Model Installation Guide

## Recommended Model: `llama3.2:3b`

**Why this model is optimal for resume-to-JD matching:**
- **Speed**: 3B parameters = very fast responses (~3-5 seconds)
- **Accuracy**: Good at text analysis and scoring tasks
- **Efficiency**: Low memory usage (~2GB RAM)
- **Reliability**: Stable JSON output
- **Size**: Small download (~2GB)

## Installation Steps

### Method 1: Using Ollama Command Line (Recommended)

1. **Open Command Prompt or PowerShell as Administrator**
2. **Run the following command:**
   ```bash
   ollama pull llama3.2:3b
   ```
3. **Wait for download to complete** (5-10 minutes depending on internet speed)
4. **Verify installation:**
   ```bash
   ollama list
   ```

### Method 2: Using Ollama Desktop App

1. **Open Ollama Desktop App**
2. **Click on "Pull a model"**
3. **Search for "llama3.2:3b"**
4. **Click "Pull" and wait for download**

### Method 3: Using API (if command line doesn't work)

1. **Open PowerShell**
2. **Run this command:**
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:11434/api/pull" -Method POST -ContentType "application/json" -Body '{"name": "llama3.2:3b"}'
   ```

## Alternative Models (if llama3.2:3b doesn't work)

### Option 1: `phi3:3.8b` (Microsoft)
```bash
ollama pull phi3:3.8b
```

### Option 2: `qwen2.5:3b` (Alibaba)
```bash
ollama pull qwen2.5:3b
```

### Option 3: `llama3.1:8b` (Meta - larger but more accurate)
```bash
ollama pull llama3.1:8b
```

## Testing the Model

After installation, test the model:

```bash
ollama run llama3.2:3b "Analyze this resume vs job description and return JSON score. Resume: Python developer with 5 years experience. Job: Senior Python Developer position."
```

## Configuration Update

Once you have a model installed, update the configuration in `backend/app/core/config.py`:

```python
ollama_model_name: str = "llama3.2:3b"  # or whatever model you installed
```

## Troubleshooting

### Issue: "ollama command not found"
**Solution**: 
1. Reinstall Ollama from https://ollama.ai
2. Restart your terminal
3. Try running `ollama --version`

### Issue: "Permission denied" during download
**Solution**:
1. Run terminal as Administrator
2. Or try using the Ollama Desktop App

### Issue: "Model not found"
**Solution**:
1. Check available models: `ollama list`
2. Try a different model from the alternatives above

## Performance Expectations

With `llama3.2:3b`:
- **Response time**: 3-5 seconds
- **Memory usage**: ~2GB RAM
- **Accuracy**: Good for resume scoring
- **JSON output**: Reliable structured responses

## Next Steps

1. Install the model using one of the methods above
2. Run the test script: `python test_qwen_integration.py`
3. Test the API endpoints
4. Monitor performance and adjust settings if needed

## Support

If you encounter issues:
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify model is installed: `ollama list`
3. Test model directly: `ollama run llama3.2:3b "Hello"`
4. Check logs in Ollama Desktop App

