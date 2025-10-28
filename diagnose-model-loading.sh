#!/bin/bash
# Diagnostic script to check model loading in running container

echo "=========================================="
echo "Model Loading Diagnostic"
echo "=========================================="
echo ""

# Check if container is running
CONTAINER_NAME="memorizer"
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '${CONTAINER_NAME}' is not running"
    echo "Please start the container first with: docker-compose -f docker-compose.airgap.yml up -d"
    exit 1
fi

echo "✅ Container is running"
echo ""

echo "1. Checking model directories:"
echo "=========================================="
docker exec ${CONTAINER_NAME} ls -lh /app/models/sentence-transformers/

echo ""
echo "2. Checking L6-v2 model structure:"
echo "=========================================="
docker exec ${CONTAINER_NAME} ls -la /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/

echo ""
echo "3. Checking if snapshot directory is accessible:"
echo "=========================================="
docker exec ${CONTAINER_NAME} python3 -c "
from pathlib import Path
model_path = Path('/app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots')
print(f'Path exists: {model_path.exists()}')
print(f'Is directory: {model_path.is_dir()}')
print(f'Can read: {model_path.stat()}')
snapshots = [d for d in model_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
print(f'Snapshots found: {len(snapshots)}')
if snapshots:
    print(f'Snapshot path: {snapshots[0]}')
    print(f'Snapshot exists: {snapshots[0].exists()}')
    print(f'Files in snapshot:')
    for f in snapshots[0].iterdir():
        print(f'  - {f.name}')
"

echo ""
echo "4. Testing model loading with SentenceTransformer:"
echo "=========================================="
docker exec ${CONTAINER_NAME} python3 -c "
import sys
sys.path.insert(0, '/app')
from pathlib import Path
from sentence_transformers import SentenceTransformer

model_path = Path('/app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots')
snapshots = [d for d in model_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

if snapshots:
    snapshot_path = snapshots[0]
    print(f'Attempting to load model from: {snapshot_path}')
    try:
        model = SentenceTransformer(str(snapshot_path), local_files_only=True)
        print('✅ Model loaded successfully!')
        print(f'Model max_seq_length: {model.max_seq_length}')
    except Exception as e:
        print(f'❌ Failed to load model: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ No snapshot directories found')
"

echo ""
echo "5. Checking environment variables:"
echo "=========================================="
docker exec ${CONTAINER_NAME} env | grep -E "(HF_|TRANSFORMERS_|MEMORIZER_|SENTENCE_)" | sort

echo ""
echo "=========================================="
echo "Diagnostic complete"
echo "=========================================="
