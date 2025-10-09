#!/bin/bash
# YI Model Upload Script for Cloudflare R2
# Prerequisites: wrangler login (run first)

set -e

BUCKET="yi-models-prod"
MODEL_DIR="/Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b"
MODEL_FILE="qwen2.5-1.5b-instruct-q4_k_m.gguf"
MANIFEST="manifest.json"

echo "🚀 YI Model Upload to Cloudflare R2"
echo "======================================"

# Check if logged in
if ! wrangler whoami &>/dev/null; then
  echo "❌ Not logged in to Cloudflare"
  echo "Run: wrangler login"
  exit 1
fi

# Create bucket if not exists
echo "📦 Creating R2 bucket: $BUCKET"
wrangler r2 bucket create "$BUCKET" || echo "Bucket already exists"

# Upload model file
echo "⬆️  Uploading model (1.0GB, may take 2-5 minutes)..."
wrangler r2 object put "$BUCKET/qwen-q4.gguf" \
  --file="$MODEL_DIR/$MODEL_FILE" \
  --content-type="application/octet-stream" \
  --cache-control="public, max-age=31536000, immutable"

# Upload manifest
echo "⬆️  Uploading manifest.json..."
wrangler r2 object put "$BUCKET/manifest.json" \
  --file="$MODEL_DIR/$MANIFEST" \
  --content-type="application/json" \
  --cache-control="public, max-age=3600"

# Verify uploads
echo "✅ Verifying uploads..."
wrangler r2 object get "$BUCKET/qwen-q4.gguf" --file=/dev/null && echo "  ✓ Model file uploaded"
wrangler r2 object get "$BUCKET/manifest.json" --file=/dev/null && echo "  ✓ Manifest uploaded"

echo ""
echo "🎉 Upload complete!"
echo "======================================"
echo "Next steps:"
echo "1. Configure custom domain in Cloudflare dashboard"
echo "2. Set domain: r2.yi-app.workers.dev"
echo "3. Enable public access"
echo "4. Test CDN URLs:"
echo "   - https://r2.yi-app.workers.dev/qwen-q4.gguf"
echo "   - https://r2.yi-app.workers.dev/manifest.json"
