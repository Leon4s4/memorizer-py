#!/bin/bash
# Diagnostic script to check if Docker image has valid model files

echo "========================================="
echo "Memorizer Docker Image Diagnostic"
echo "========================================="
echo ""

IMAGE=${1:-leonasa/memorizer-py:latest}

echo "Checking image: $IMAGE"
echo ""

echo "1. Checking if image exists..."
if ! docker image inspect "$IMAGE" &>/dev/null; then
    echo "❌ Image not found: $IMAGE"
    exit 1
fi
echo "✅ Image found"
echo ""

echo "2. Checking model file sizes..."
docker run --rm "$IMAGE" sh -c 'du -sh /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-* 2>/dev/null' || echo "❌ Model directories not found"
echo ""

echo "3. Checking if blob files are actual JSON (not LFS pointers)..."
echo "Checking config.json blob..."
CONTENT=$(docker run --rm "$IMAGE" cat /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/blobs/72b987fd805cfa2b58c4c8c952b274a11bfd5a00 2>/dev/null | head -c 50)

if [[ "$CONTENT" == *"version https://git-lfs"* ]]; then
    echo "❌ PROBLEM: Blob file is a Git LFS pointer!"
    echo "Content: $CONTENT"
elif [[ "$CONTENT" == "{"* ]]; then
    echo "✅ Blob file is valid JSON"
    echo "Content preview: $CONTENT"
else
    echo "⚠️  Unexpected content: $CONTENT"
fi
echo ""

echo "4. Checking embeddings.py for local_files_only parameter..."
LINES=$(docker run --rm "$IMAGE" grep -n "local_files_only" /app/services/embeddings.py 2>/dev/null)
if [ -z "$LINES" ]; then
    echo "❌ PROBLEM: embeddings.py does NOT have local_files_only parameter"
    echo "This image was built from old code!"
else
    echo "✅ embeddings.py has local_files_only:"
    echo "$LINES"
fi
echo ""

echo "5. Testing model loading..."
echo "Attempting to load model..."
docker run --rm "$IMAGE" python3 -c "
from sentence_transformers import SentenceTransformer
try:
    model = SentenceTransformer('/app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf', local_files_only=True)
    print('✅ Model loaded successfully')
except Exception as e:
    print(f'❌ FAILED: {e}')
    import sys
    sys.exit(1)
" 2>&1
echo ""

echo "========================================="
echo "Diagnostic Complete"
echo "========================================="
