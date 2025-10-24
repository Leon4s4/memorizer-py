# Docker Hub Deployment Setup

This guide explains how to set up automatic Docker image builds and deployment to Docker Hub using GitHub Actions.

## Prerequisites

1. **Docker Hub Account** - Sign up at https://hub.docker.com if you don't have one
2. **Docker Hub Repository** - Create a repository (e.g., `yourusername/memorizer`)
3. **GitHub Repository** - This repository with the workflow configured

## Step 1: Create Docker Hub Access Token

1. Log in to Docker Hub (https://hub.docker.com)
2. Go to **Account Settings** → **Security** → **Access Tokens**
3. Click **New Access Token**
4. Give it a name (e.g., `github-actions-memorizer`)
5. Set permissions: **Read, Write, Delete**
6. Click **Generate**
7. **IMPORTANT:** Copy the token immediately (you won't be able to see it again)

## Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

   **Secret 1:**
   - Name: `DOCKERHUB_USERNAME`
   - Value: Your Docker Hub username (e.g., `johndoe`)

   **Secret 2:**
   - Name: `DOCKERHUB_TOKEN`
   - Value: The access token you generated in Step 1

## Step 3: Verify Workflow Configuration

The workflow file is located at `.github/workflows/docker-publish.yml` and is configured to:

### Trigger Conditions
- **Push to main/master branch** - Builds and pushes with `latest` tag
- **Push tags (v*.*.*)** - Builds and pushes with semantic version tags
- **Pull requests** - Builds only (doesn't push)
- **Manual trigger** - Via GitHub Actions UI

### Image Tags Generated

| Trigger | Tags Created |
|---------|-------------|
| Push to `main` | `latest`, `main-<sha>` |
| Push tag `v1.2.3` | `1.2.3`, `1.2`, `1`, `latest` |
| Push to `feature-x` branch | `feature-x`, `feature-x-<sha>` |
| Pull request #42 | `pr-42` (build only, not pushed) |

### Multi-Platform Support
The workflow builds for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, including Apple Silicon)

## Step 4: Test the Workflow

### Option A: Push to main branch
```bash
git add .
git commit -m "Add Docker Hub workflow"
git push origin main
```

### Option B: Create a version tag
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Option C: Manual trigger
1. Go to **Actions** tab in GitHub
2. Select **Build and Push to Docker Hub**
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Step 5: Monitor the Build

1. Go to the **Actions** tab in your GitHub repository
2. Click on the workflow run
3. Monitor the build progress
4. Check for any errors

Expected build time: **15-25 minutes** (due to model downloads and multi-platform builds)

## Step 6: Verify on Docker Hub

1. Go to Docker Hub: https://hub.docker.com
2. Navigate to your repository
3. Verify the tags are present
4. Check the image details

## Using the Published Image

Once published, anyone can use your image:

```bash
# Pull the latest version
docker pull yourusername/memorizer:latest

# Pull a specific version
docker pull yourusername/memorizer:1.2.3

# Run the container
docker run -d \
  -p 8000:8000 \
  -p 8501:8501 \
  -v memorizer-data:/app/data \
  --name memorizer \
  yourusername/memorizer:latest
```

## Workflow Features

### ✅ Automated Builds
- Triggers on push to main/master
- Triggers on version tags
- Manual trigger available

### ✅ Multi-Platform
- Supports AMD64 and ARM64 architectures
- Works on Intel, AMD, and Apple Silicon

### ✅ Caching
- Uses GitHub Actions cache for faster builds
- Reduces build time significantly on subsequent runs

### ✅ Security
- Uses short-lived tokens (not passwords)
- Secrets are encrypted in GitHub
- Attestation for supply chain security

### ✅ Tagging Strategy
- Semantic versioning support
- Branch-based tags for development
- Latest tag for main branch
- SHA tags for traceability

## Troubleshooting

### Build Fails: "Authentication required"
- Verify `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are set correctly
- Check that the token has **Read, Write, Delete** permissions
- Ensure the token hasn't expired

### Build Fails: "repository does not exist"
- Create the repository on Docker Hub first
- Ensure the repository name matches `yourusername/memorizer`
- Update `DOCKER_IMAGE` in the workflow if using a different name

### Build is Slow
- First build takes ~20-25 minutes (downloads models)
- Subsequent builds are faster due to caching
- Multi-platform builds take longer than single-platform

### Want to Push to Different Registry?
Edit `.github/workflows/docker-publish.yml`:
- Change `DOCKER_IMAGE` environment variable
- Update login action for your registry (GitHub Container Registry, etc.)

## Customization

### Change Docker Hub Username/Repository

Edit the workflow file and update:
```yaml
env:
  DOCKER_IMAGE: yourname/yourrepo  # Change this
```

Or use the existing setup with secrets (recommended).

### Build for Single Platform (Faster)

Edit the workflow and change:
```yaml
env:
  PLATFORMS: linux/amd64  # Remove linux/arm64
```

### Add More Triggers

Add more branches or patterns:
```yaml
on:
  push:
    branches:
      - main
      - develop      # Add more branches
      - release/*    # Match patterns
```

## Best Practices

1. **Use Semantic Versioning** - Tag releases as `v1.0.0`, `v1.1.0`, etc.
2. **Test Before Tagging** - Ensure the build works on main before creating version tags
3. **Monitor Build Times** - First build is slow; subsequent builds should be faster
4. **Rotate Tokens** - Regenerate Docker Hub tokens periodically
5. **Use Protected Branches** - Protect main/master branch to prevent accidental pushes

## Example Release Workflow

```bash
# 1. Make changes and test locally
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "Add new feature"

# 2. Create PR and merge to main
git push origin feature/new-feature
# Create PR on GitHub, get review, merge

# 3. Tag the release
git checkout main
git pull origin main
git tag v1.1.0
git push origin v1.1.0

# 4. GitHub Actions automatically builds and pushes:
# - yourusername/memorizer:1.1.0
# - yourusername/memorizer:1.1
# - yourusername/memorizer:1
# - yourusername/memorizer:latest
```

## Cost Considerations

- **GitHub Actions**: Free for public repositories (2,000 minutes/month for private)
- **Docker Hub**: Free tier includes unlimited public repositories
- **Build time**: ~20-25 minutes per build (counts against GitHub Actions minutes)

## Support

If you encounter issues:
1. Check GitHub Actions logs for error messages
2. Verify Docker Hub credentials and permissions
3. Ensure the Dockerfile builds locally: `docker build -t memorizer:test .`
4. Check GitHub Actions status page: https://www.githubstatus.com/
5. Check Docker Hub status page: https://status.docker.com/

---

**Ready to deploy?** Just push to main or create a version tag, and GitHub Actions will handle the rest! 🚀
