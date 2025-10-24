# Deployment Guide

Quick reference for deploying Memorizer to various platforms.

## Docker Hub (Automated via GitHub Actions)

### Setup (One-time)
1. Create Docker Hub account and repository
2. Generate Docker Hub access token
3. Add GitHub secrets: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
4. See detailed instructions: [.github/DOCKER_HUB_SETUP.md](.github/DOCKER_HUB_SETUP.md)

### Deploy New Version
```bash
# Automatic deployment on version tag
git tag v1.0.0
git push origin v1.0.0

# Or push to main for latest tag
git push origin main
```

### Using Published Image
```bash
# Pull and run from Docker Hub
docker pull yourusername/memorizer:latest
docker run -d -p 8000:8000 -p 8501:8501 \
  -v memorizer-data:/app/data \
  --name memorizer \
  yourusername/memorizer:latest
```

## Local Development

```bash
# Quick start
./run-local.sh

# Or step by step
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python api.py &
streamlit run app.py
```

## Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Considerations

### Environment Variables
Create `.env` file from `.env.example`:
```bash
cp .env.example .env
# Edit .env with production values
```

### Data Persistence
- Mount `/app/data` volume for persistent storage
- Regular backups of ChromaDB data
- Monitor disk usage (embeddings grow over time)

### Security
- Add authentication to REST API (not included by default)
- Use HTTPS/TLS in production
- Restrict CORS origins
- Secure Docker Hub tokens

### Monitoring
- Health check: `http://localhost:8000/healthz`
- Metrics: Check `/api/stats` endpoint
- Logs: Use `docker logs` or centralized logging

### Scaling
- Memorizer is currently single-instance
- For multi-instance: Need shared storage (NFS, S3)
- Consider external ChromaDB for better scaling

## Deployment Targets

| Target | Method | Best For |
|--------|--------|----------|
| **Development** | `./run-local.sh` | Local testing |
| **Testing** | `docker-compose up` | Integration testing |
| **Production** | Docker Hub + Pull | Simple deployment |
| **Cloud** | GitHub Actions → Registry → K8s | Enterprise scale |

## CI/CD Pipeline

```
Code Push → GitHub Actions → Build Multi-Platform → Push to Docker Hub → Deploy
```

Builds trigger on:
- Push to main/master → `latest` tag
- Version tags (v*.*.*) → Semantic version tags
- Manual workflow dispatch → Custom deployment

## Quick Commands Reference

```bash
# Local
make install          # Install dependencies
make run             # Run locally
make clean           # Clean artifacts

# Docker
make build           # Build image
make docker-run      # Run container
make docker-stop     # Stop container

# Models
make models          # Download LLM model
./download-models.sh # Interactive model download

# Compose
make compose-up      # Start with compose
make compose-down    # Stop compose
make compose-logs    # View logs
```

## Troubleshooting

**Ports already in use:**
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :8501

# Kill the processes or change ports in docker-compose.yml
```

**Models not found:**
```bash
# Download models manually
./download-models.sh

# Or let Docker download during build (takes longer)
```

**ChromaDB errors:**
```bash
# Clear ChromaDB data
rm -rf data/chroma
# Restart services
```

**GitHub Actions build fails:**
- Check Docker Hub credentials in GitHub secrets
- Verify workflow file syntax
- Check GitHub Actions logs for details
- See [.github/DOCKER_HUB_SETUP.md](.github/DOCKER_HUB_SETUP.md)

## Next Steps

1. ✅ Set up GitHub Actions (if deploying to Docker Hub)
2. ✅ Configure environment variables
3. ✅ Test deployment locally
4. ✅ Deploy to production
5. ✅ Set up monitoring and backups
6. ✅ Configure MCP for Claude Desktop/Code

See [CLAUDE.md](CLAUDE.md) for detailed architecture and development guide.
