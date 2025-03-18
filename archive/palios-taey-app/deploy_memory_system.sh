#!/bin/bash
# deploy_memory_system.sh
# Deploys the PALIOS-TAEY Memory System to Google Cloud Platform

set -e  # Exit on any error

# Configuration
PROJECT_ID=${PROJECT_ID:-"palios-taey-dev"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"palios-taey-service"}
IMAGE_NAME="palios-taey"
TAG=${TAG:-"memory-integration"}

# Display configuration
echo "Deploying PALIOS-TAEY Memory System with configuration:"
echo "  Project ID:   $PROJECT_ID"
echo "  Region:       $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image:        $IMAGE_NAME:$TAG"
echo ""

# Ensure gcloud is set to the correct project
echo "Setting gcloud project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Build the container image
echo "Building container image..."
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/palios-taey/$IMAGE_NAME:$TAG

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/palios-taey/$IMAGE_NAME:$TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,ENVIRONMENT=dev,COLLECTION_PREFIX=memory_"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')
echo ""
echo "Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo ""

# Verify the deployment
echo "Verifying deployment..."
curl -s $SERVICE_URL/health

echo ""
echo "To run the verification tests against the deployed service:"
echo "export API_URL=$SERVICE_URL"
echo "export API_KEY=test_key"
echo "python verify_memory.py"
