#!/bin/bash
# Verify both AMD64 and ARM64 images are air-gapped

set -e

IMAGE="leonasa/memorizer-py:latest"

echo "========================================="
echo "Verifying Both Architectures"
echo "========================================="
echo ""

# Function to check an architecture
check_architecture() {
    local ARCH=$1
    echo "========================================="
    echo "Checking ${ARCH} image"
    echo "========================================="

    echo "1. Environment variables:"
    docker run --rm --platform linux/${ARCH} ${IMAGE} env | grep -E "HF_|TRANSFORMERS_" | sort
    echo ""

    echo "2. Network monitor exists:"
    docker run --rm --platform linux/${ARCH} ${IMAGE} ls -la /app/services/network_monitor.py 2>&1 | tail -1
    echo ""

    echo "3. local_files_only count:"
    docker run --rm --platform linux/${ARCH} ${IMAGE} grep -c "local_files_only" /app/services/embeddings.py
    echo ""

    echo "4. Model sizes:"
    docker run --rm --platform linux/${ARCH} ${IMAGE} sh -c 'du -sh /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-* 2>/dev/null'
    echo ""

    echo "5. LLM model:"
    docker run --rm --platform linux/${ARCH} ${IMAGE} ls -lh /app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf | awk '{print $5, $9}'
    echo ""

    echo "6. Check for any download code in Dockerfile:"
    docker run --rm --platform linux/${ARCH} ${IMAGE} cat /app/Dockerfile | grep -i "download\|curl.*http\|wget.*http" || echo "No download commands found ✅"
    echo ""
}

# Check both architectures
check_architecture "amd64"
echo ""
echo ""
check_architecture "arm64"

echo "========================================="
echo "Comparison Complete"
echo "========================================="
echo ""
echo "Both architectures should show:"
echo "  ✅ HF_HUB_OFFLINE=1"
echo "  ✅ TRANSFORMERS_OFFLINE=1"
echo "  ✅ network_monitor.py exists"
echo "  ✅ local_files_only count = 6"
echo "  ✅ Models: ~88M and ~129M"
echo "  ✅ LLM: 638M"
