#!/bin/bash
set -e

# PALIOS-TAEY simplified deployment script
# This script handles the complete deployment process to Google Cloud Platform

# Configuration
PROJECT_ID="palios-taey-dev"
REGION="us-central1"
SERVICE_NAME="palios-taey"
ARTIFACT_REPO="palios-taey-repo"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${SERVICE_NAME}"
MAX_INSTANCES=10
MEMORY="1Gi"
CPU=1
TIMEOUT="3600s"

echo "===== PALIOS-TAEY Deployment ====="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Run environment fix script
echo "Fixing environment configuration..."
./fix_environment_config.sh

# Ensure we're using the correct GCP project
gcloud config set project ${PROJECT_ID}
echo "✅ Project configured"

# Ensure required APIs are enabled
echo "Enabling required APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com

# Create Artifact Registry repository if it doesn't exist
if ! gcloud artifacts repositories describe ${ARTIFACT_REPO} --location=${REGION} &>/dev/null; then
  echo "Creating Artifact Registry repository..."
  gcloud artifacts repositories create ${ARTIFACT_REPO} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Repository for PALIOS-TAEY images"
  echo "✅ Artifact Registry repository created"
else
  echo "✅ Artifact Registry repository already exists"
fi

# Configure Docker to use Artifact Registry
echo "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Use Cloud Build
echo "Building and pushing with Cloud Build..."
gcloud builds submit --tag=${IMAGE_NAME} .
echo "✅ Docker image built and pushed: ${IMAGE_NAME}"

# Initialize Firestore if needed
if ! gcloud firestore databases describe --project=${PROJECT_ID} &>/dev/null; then
  echo "Creating Firestore database..."
  gcloud firestore databases create --region=${REGION} --project=${PROJECT_ID}
  echo "✅ Firestore database created"
else
  echo "✅ Firestore database already exists"
fi

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --memory ${MEMORY} \
  --cpu ${CPU} \
  --timeout ${TIMEOUT} \
  --max-instances ${MAX_INSTANCES} \
  --allow-unauthenticated \
  --update-env-vars "PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production,USE_MOCK_RESPONSES=true"

echo "✅ Deployed to Cloud Run"

# Display deployed service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "===== Deployment Complete ====="
echo "Service URL: ${SERVICE_URL}"
echo "Health Check: ${SERVICE_URL}/health"
