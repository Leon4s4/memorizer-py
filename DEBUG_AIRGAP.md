# Debugging Air-Gapped Deployment Issues

This document explains how to debug network connection issues in air-gapped deployments.

## Comprehensive Logging Enabled

The latest version includes extensive logging to identify exactly where and why any HuggingFace connections are attempted.

### What Gets Logged

1. **Environment Variables** - All HF-related env vars at startup
2. **Model Loading Steps** - Every step of the model loading process
3. **Network Requests** - ANY HTTP/HTTPS request attempt with full stack trace

### How to View Logs

```bash
# View live logs
docker logs -f memorizer

# View last 200 lines
docker logs memorizer --tail 200

# Save logs to file for analysis
docker logs memorizer > memorizer-debug.log 2>&1
```

### What to Look For

#### 1. Environment Variables Section
Look for this at startup:
```
================================================================================
EMBEDDING SERVICE ENVIRONMENT:
MEMORIZER_ENVIRONMENT: production
HF_HUB_OFFLINE: 1
TRANSFORMERS_OFFLINE: 1
HF_DATASETS_OFFLINE: 1
SENTENCE_TRANSFORMERS_HOME: /app/models/sentence-transformers
HF_HOME: NOT SET
================================================================================
```

**Expected values for air-gapped:**
- `HF_HUB_OFFLINE: 1`
- `TRANSFORMERS_OFFLINE: 1`
- `HF_DATASETS_OFFLINE: 1`

**If NOT SET:** The environment variables are not being passed to the container!

#### 2. Network Monitor Installation
```
================================================================================
INSTALLING NETWORK MONITOR
All HTTP/HTTPS requests will be logged
================================================================================
✅ requests library patched for monitoring
✅ httpx library patched for monitoring
Network monitor installation complete
```

#### 3. Model Loading Process
```
================================================================================
LOADING PRIMARY MODEL: all-MiniLM-L6-v2
================================================================================
Checking model cache path: /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots
Path exists: True
Found 1 snapshot directories
Using snapshot path: /app/models/sentence-transformers/.../c9745ed1d9f207416be6d2e6f8de32d1f16199bf
Snapshot path exists: True
Calling SentenceTransformer('.../c9745ed1d9f207416be6d2e6f8de32d1f16199bf', local_files_only=True)
✅ Primary embedding model loaded successfully from snapshot
```

#### 4. Network Request Detection (This Should NOT Appear!)
If you see this, it means something is trying to connect:
```
================================================================================
⚠️  NETWORK REQUEST DETECTED!
URL: https://huggingface.co/...
Data: None
Timeout: None
================================================================================
Call stack:
... (full stack trace showing where the call originated)
================================================================================
```

## Troubleshooting Steps

### Issue: Environment Variables Not Set

**Symptom:**
```
HF_HUB_OFFLINE: NOT SET
TRANSFORMERS_OFFLINE: NOT SET
```

**Solution:**
Make sure you're using the correct docker-compose file:
```bash
# For air-gapped deployment, use:
docker-compose -f docker-compose.airgap.yml up -d

# NOT just:
docker-compose up -d
```

Or if running with `docker run`, ensure all environment variables are set:
```bash
docker run -d \
  -e MEMORIZER_ENVIRONMENT=production \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e HF_DATASETS_OFFLINE=1 \
  -e CHROMA_TELEMETRY_IMPL=none \
  -e PYTORCH_ENABLE_MPS_FALLBACK=1 \
  -e TRANSFORMERS_VERBOSITY=error \
  -e TOKENIZERS_PARALLELISM=false \
  -p 8000:8000 -p 8501:8501 -p 8800:8800 \
  -v memorizer-data:/app/data \
  --name memorizer \
  leonasa/memorizer-py:latest
```

### Issue: Wrong Docker Image

**Symptom:**
- embeddings.py shows line 37 in error (not line 59)
- No network monitor logs

**Solution:**
You're running an old image. Pull the latest:
```bash
# On internet-connected machine:
docker pull leonasa/memorizer-py:latest
docker save leonasa/memorizer-py:latest -o memorizer-latest.tar

# Transfer to air-gapped machine, then:
docker load -i memorizer-latest.tar
```

Verify you have the latest image:
```bash
docker run --rm leonasa/memorizer-py:latest grep -c "local_files_only" /app/services/embeddings.py
# Should output: 4

docker run --rm leonasa/memorizer-py:latest ls -la /app/services/network_monitor.py
# Should show the file exists
```

### Issue: Network Requests Still Happening

**Symptom:**
```
⚠️  NETWORK REQUEST DETECTED!
URL: https://huggingface.co/...
```

**Action:**
1. Check the full stack trace in the logs - it will show exactly which library and line of code is making the request
2. Save the complete log output
3. Report the issue with the stack trace

The stack trace will look like:
```
Call stack:
  File "/app/services/embeddings.py", line 59, in _load_models
    self._model_primary = SentenceTransformer(str(snapshot_path), local_files_only=True)
  File "/home/memorizer/.local/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 123, in __init__
    ... (shows exact line attempting network access)
```

This tells us EXACTLY where to fix the issue.

## Quick Diagnostic Command

Run this on your air-gapped machine to get all relevant info:
```bash
echo "=== Docker Image Info ===" && \
docker image inspect leonasa/memorizer-py:latest --format='{{.Created}}' && \
echo "" && \
echo "=== Environment Check ===" && \
docker run --rm leonasa/memorizer-py:latest env | grep -E "HF_|TRANSFORMERS_|MEMORIZER_" && \
echo "" && \
echo "=== Code Version Check ===" && \
docker run --rm leonasa/memorizer-py:latest grep -c "local_files_only" /app/services/embeddings.py && \
echo "" && \
echo "=== Network Monitor Check ===" && \
docker run --rm leonasa/memorizer-py:latest ls -la /app/services/network_monitor.py
```

## Expected Output

When everything is working correctly:
1. ✅ Environment variables are all set to `1`
2. ✅ Network monitor installs successfully
3. ✅ Models load from local snapshots
4. ✅ **NO network request warnings**
5. ✅ Container starts and runs without errors

## Getting Help

When reporting issues, please include:
1. Output of the diagnostic command above
2. Full container logs: `docker logs memorizer > logs.txt 2>&1`
3. How you started the container (docker-compose file or docker run command)
4. Whether you're on the air-gapped machine or testing locally
