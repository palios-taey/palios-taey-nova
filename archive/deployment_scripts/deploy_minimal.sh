#!/bin/bash
set -e

# Minimal PALIOS-TAEY deployment script
PROJECT_ID="palios-taey-dev"
REGION="us-central1"
SERVICE_NAME="palios-taey"
ARTIFACT_REPO="palios-taey-repo"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${SERVICE_NAME}"

# Configure project
gcloud config set project ${PROJECT_ID}

# Check if we have a successful build already
BUILD_IMAGE=$(gcloud builds list --filter="status=SUCCESS" --format="value(results.images.name)" --limit=1)

if [ -n "$BUILD_IMAGE" ]; then
  echo "Using existing successful build: $BUILD_IMAGE"
  IMAGE_NAME=$BUILD_IMAGE
else
  echo "No successful build found. Creating a new one."
  
  # Create minimal environment_config.py if it doesn't exist
  if [ ! -f "src/environment_config.py" ]; then
    mkdir -p src
    cat > src/environment_config.py << 'EOF'
"""Environment configuration for PALIOS-TAEY"""
import os
def initialize_environment():
    os.makedirs('logs', exist_ok=True)
EOF
    echo "Created minimal environment_config.py"
  fi

  # Submit a smaller build with limited files
  echo "Building with limited files..."
  gcloud builds submit --tag=${IMAGE_NAME} --timeout=10m \
    --substitutions=_IGNORE_PATTERNS="**.git/**,**.md,**.bak,scripts/**"
fi

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600s \
  --max-instances 10 \
  --allow-unauthenticated \
  --update-env-vars "PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production,USE_MOCK_RESPONSES=true" \
  --port=8080

# Display service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "Service URL: ${SERVICE_URL}"
