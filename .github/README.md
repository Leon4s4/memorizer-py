# GitHub Actions Workflow

## Overview

This repository uses GitHub Actions to automatically build and push Docker images to Docker Hub.

## Workflow: Build and Push to Docker Hub

**File:** `.github/workflows/docker-publish.yml`

### How It Works

The workflow uses a **split platform build strategy** for maximum reliability:

1. **Job 1: build-amd64**
   - Builds the Docker image for AMD64 (Intel/AMD processors)
   - Frees up ~10GB disk space before building
   - Pushes to Docker Hub by digest

2. **Job 2: build-arm64**
   - Builds the Docker image for ARM64 (Apple Silicon, ARM servers)
   - Runs in parallel with build-amd64
   - Frees up ~10GB disk space before building
   - Pushes to Docker Hub by digest

3. **Job 3: merge**
   - Waits for both platform builds to complete
   - Creates a multi-platform manifest
   - Tags the final image with all requested tags

### Advantages

✅ **Reliable** - Each job gets fresh 14GB disk space
✅ **Fast** - Parallel builds (15-20 minutes total)
✅ **Efficient** - Better caching per platform
✅ **Multi-platform** - Single `docker pull` works on AMD64 and ARM64

### Triggers

The workflow runs on:
- **Push to main/master** → Tags with `latest` + branch name
- **Version tags (v*.*.*)** → Tags with semantic versions
- **Pull requests** → Builds only (doesn't push)
- **Manual trigger** → Via GitHub Actions UI

### Setup

See the main README or documentation for setup instructions:
1. Create Docker Hub account and repository
2. Generate Docker Hub access token
3. Add GitHub secrets: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`

### Monitoring

Go to the **Actions** tab to see:
- 3 jobs running (2 builds + 1 merge)
- Real-time logs for each job
- Disk space before/after cleanup
- Build progress and errors

### Troubleshooting

If builds fail:
1. Check the job logs in GitHub Actions
2. Verify Docker Hub credentials are correct
3. Ensure the repository name matches in secrets
4. See DEPLOYMENT.md for more help

### Air-Gapped Builds

The Docker images are **fully air-gapped**:
- ✅ Embedding model (all-MiniLM-L6-v2) pre-downloaded during build
- ✅ LLM model (TinyLlama 1.1B) pre-downloaded during build
- ✅ No internet required at runtime
- ✅ Can run with `--network none`

Image size: ~2GB (includes all models)

### Disk Space Management

Each build job includes automatic cleanup that removes:
- .NET SDK (~2GB)
- Android SDK (~3GB)
- Haskell compiler (~2GB)
- CodeQL tools (~1GB)
- Docker cache (~2GB)

**Total freed:** ~10GB per job

This prevents "no space left on device" errors.

---

For more details, see:
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment guide
- [CLAUDE.md](../CLAUDE.md) - Development guide
- [Dockerfile](../Dockerfile) - Image definition
