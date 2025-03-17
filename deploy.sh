#!/bin/bash
set -e

# PALIOS-TAEY deployment script
# This script handles the complete deployment process to Google Cloud Platform

# Configuration
PROJECT_ID="palios-taey-dev"
REGION="us-central1"
SERVICE_NAME="palios-taey"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MAX_INSTANCES=10
MEMORY="1Gi"
CPU=1
TIMEOUT="3600s"

echo "===== PALIOS-TAEY Deployment ====="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

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

echo "✅ APIs enabled"

# Build Docker image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} .
echo "✅ Docker image built: ${IMAGE_NAME}"

# Initialize Firestore if needed
if ! gcloud firestore databases describe --project=${PROJECT_ID} 2>/dev/null; then
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
  --update-env-vars "PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production,USE_MOCK_RESPONSES=false" \
  --service-account="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "✅ Deployed to Cloud Run"

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe ${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
  echo "Creating service account..."
  gcloud iam service-accounts create ${SERVICE_NAME} \
    --display-name="PALIOS-TAEY Service Account"
  echo "✅ Service account created"
else
  echo "✅ Service account already exists"
fi

# Grant necessary permissions
echo "Granting permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

echo "✅ Permissions granted"

# Display deployed service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "===== Deployment Complete ====="
echo "Service URL: ${SERVICE_URL}"
echo "Health Check: ${SERVICE_URL}/health"
