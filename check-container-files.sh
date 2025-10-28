#!/bin/bash
# Simple diagnostic for Windows - checks actual container contents

echo "1. Check if /app/models exists:"
docker exec memorizer ls -la /app/models/

echo ""
echo "2. Check if sentence-transformers directory exists:"
docker exec memorizer ls -la /app/models/sentence-transformers/ || echo "Directory does not exist!"

echo ""
echo "3. Check what image the container is using:"
docker inspect memorizer --format='{{.Config.Image}}'

echo ""
echo "4. Check when the container was created:"
docker inspect memorizer --format='{{.Created}}'

echo ""
echo "5. Check if there's a volume mounted over /app/models:"
docker inspect memorizer --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

echo ""
echo "6. Try to find model files anywhere in /app:"
docker exec memorizer find /app -name "all-MiniLM-L6-v2" -o -name "models--sentence-transformers*" 2>/dev/null || echo "Not found"

echo ""
echo "7. Check disk usage of /app/models:"
docker exec memorizer du -sh /app/models/ 2>/dev/null || echo "Cannot access"
