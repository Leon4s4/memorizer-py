# Air-Gapped Deployment Guide

This guide explains how to deploy Memorizer on a machine **without internet access**.

## Why Air-Gapped Deployment?

Memorizer is designed to work completely offline once deployed. However, the Docker build process normally requires internet to:
1. Pull the Python base image (`python:3.11-slim`)
2. Download Python packages (already bundled in requirements.txt)
3. Download ML models (already committed to git)

## Prerequisites

- **Two machines**: One with internet ("online"), one without ("air-gapped")
- Docker installed on both machines
- USB drive or network transfer capability

## Method 1: Transfer Complete Docker Image (Recommended)

### On Online Machine

```bash
# Pull the latest pre-built image from Docker Hub
docker pull leon4s4/memorizer-py:latest

# Save to tar file (~2GB)
docker save leon4s4/memorizer-py:latest -o memorizer-latest.tar

# Transfer memorizer-latest.tar to air-gapped machine via USB/network
```

### On Air-Gapped Machine

```bash
# Load the image
docker load -i memorizer-latest.tar

# Run using the air-gapped docker-compose file
docker-compose -f docker-compose.airgap.yml up -d
```

**Ports:**
- API: http://localhost:9000
- UI: http://localhost:8501
- MCP: http://localhost:8800/mcp

## Method 2: Build from Source (Advanced)

If you need to build from source on the air-gapped machine:

### On Online Machine

```bash
# 1. Pull and save base image
docker pull python:3.11-slim
docker save python:3.11-slim -o python-3.11-slim.tar

# 2. Clone the repository
git clone https://github.com/Leon4s4/memorizer-py.git
cd memorizer-py

# 3. Transfer BOTH files to air-gapped machine:
#    - python-3.11-slim.tar
#    - memorizer-py/ (entire directory)
```

### On Air-Gapped Machine

```bash
# 1. Load base image
docker load -i python-3.11-slim.tar

# 2. Verify base image is loaded
docker images | grep python

# 3. Build Memorizer
cd memorizer-py
docker-compose build

# 4. Run
docker-compose up -d
```

## Updating the Application

To update to a newer version on air-gapped machine:

### On Online Machine

```bash
# Pull latest version
docker pull leon4s4/memorizer-py:latest

# Save to tar
docker save leon4s4/memorizer-py:latest -o memorizer-latest.tar

# Transfer to air-gapped machine
```

### On Air-Gapped Machine

```bash
# Stop current version
docker-compose -f docker-compose.airgap.yml down

# Load new version
docker load -i memorizer-latest.tar

# Start new version
docker-compose -f docker-compose.airgap.yml up -d
```

## Verifying Air-Gapped Operation

Once deployed, Memorizer requires **zero internet connectivity**:

✅ All ML models are bundled in the image
✅ All Python dependencies are pre-installed
✅ Embedding model (all-MiniLM-L6-v2) is included
✅ LLM model (TinyLlama 1.1B) is included
✅ ChromaDB runs locally

Test by disconnecting network and running:

```bash
curl http://localhost:9000/healthz
# Should return: {"status":"healthy","version":"2.0.0"}

curl http://localhost:8800/mcp
# Should return MCP server info
```

## Troubleshooting

### Error: "failed to resolve source metadata"

This means Docker is trying to pull images from the internet. Ensure:
1. Base image is loaded: `docker images | grep python`
2. Using correct docker-compose file: `docker-compose.airgap.yml`

### Data Persistence

Data is stored in Docker volume `memorizer-data`. To backup:

```bash
# Backup
docker run --rm -v memorizer-data:/data -v $(pwd):/backup ubuntu tar czf /backup/memorizer-backup.tar.gz -C /data .

# Restore
docker run --rm -v memorizer-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/memorizer-backup.tar.gz -C /data
```

## Security Notes

Air-gapped deployment provides:
- **No telemetry**: All ChromaDB telemetry is disabled
- **No external calls**: Application never contacts external services
- **Local processing**: All embeddings and LLM inference run locally

Perfect for:
- Classified/sensitive environments
- Compliance requirements (HIPAA, SOC2, etc.)
- Offline research stations
- High-security deployments
