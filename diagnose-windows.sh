#!/bin/bash
# Run this on your Windows machine to diagnose the issue

echo "=========================================="
echo "Diagnosing Model Loading Issue"
echo "=========================================="
echo ""

# Find the container name
CONTAINER=$(docker ps --format '{{.Names}}' | grep memorizer | head -1)

if [ -z "$CONTAINER" ]; then
    echo "❌ No memorizer container found running"
    exit 1
fi

echo "✅ Found container: $CONTAINER"
echo ""

echo "1. Checking if models directory exists:"
echo "=========================================="
docker exec $CONTAINER ls -lh /app/models/sentence-transformers/ 2>&1

echo ""
echo "2. Checking L6-v2 snapshots:"
echo "=========================================="
docker exec $CONTAINER ls -la /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/ 2>&1

echo ""
echo "3. Checking snapshot contents:"
echo "=========================================="
docker exec $CONTAINER sh -c 'ls -la /app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*/' 2>&1

echo ""
echo "4. Testing Python model detection:"
echo "=========================================="
docker exec $CONTAINER python3 << 'PYTHON'
from pathlib import Path
import os

print(f"Current working directory: {os.getcwd()}")
print(f"User: {os.getenv('USER')}")
print()

model_path = Path('/app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots')
print(f"Model path: {model_path}")
print(f"Path exists: {model_path.exists()}")
print(f"Path is dir: {model_path.is_dir()}")

if model_path.exists():
    print(f"\nContents of {model_path}:")
    for item in model_path.iterdir():
        print(f"  {item.name} - is_dir: {item.is_dir()}, starts_with_dot: {item.name.startswith('.')}")

    snapshots = [d for d in model_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    print(f"\nFiltered snapshots: {len(snapshots)}")

    if snapshots:
        snapshot = snapshots[0]
        print(f"Using snapshot: {snapshot}")
        print(f"\nSnapshot contents:")
        for item in snapshot.iterdir():
            stat = item.stat()
            print(f"  {item.name} - size: {stat.st_size} bytes")
else:
    print("❌ Model path does not exist!")
PYTHON

echo ""
echo "5. Checking environment variables in container:"
echo "=========================================="
docker exec $CONTAINER env | grep -E "(HF_|TRANSFORMERS_|MEMORIZER_|SENTENCE_)" | sort

echo ""
echo "6. Attempting to load model with error details:"
echo "=========================================="
docker exec $CONTAINER python3 << 'PYTHON'
import sys
sys.path.insert(0, '/app')

from pathlib import Path
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.DEBUG)

model_path = Path('/app/models/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/snapshots')
snapshots = [d for d in model_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

if snapshots:
    snapshot = snapshots[0]
    print(f"Attempting to load from: {snapshot}")
    print(f"Files present:")
    for f in snapshot.iterdir():
        print(f"  - {f.name}")
    print()

    try:
        print("Loading model with local_files_only=True...")
        model = SentenceTransformer(str(snapshot), local_files_only=True)
        print("✅ SUCCESS! Model loaded")
    except FileNotFoundError as e:
        print(f"❌ FileNotFoundError: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Other error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ No snapshots found")
PYTHON

echo ""
echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
