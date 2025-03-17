#!/bin/bash
# deploy.sh
# Deploys the PALIOS-TAEY system to Google Cloud Platform

set -e  # Exit on any error

# Configuration
PROJECT_ID=${PROJECT_ID:-"palios-taey-dev"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"palios-taey-service"}
IMAGE_NAME="palios-taey"
TAG=${TAG:-"v1"}

# Display configuration
echo "Deploying PALIOS-TAEY with configuration:"
echo "  Project ID:   $PROJECT_ID"
echo "  Region:       $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image:        $IMAGE_NAME:$TAG"
echo ""

# Prepare the source directory structure
echo "Preparing source directory structure..."
mkdir -p src/palios_taey/models src/palios_taey/routing

# Copy necessary source files from the repository
# This ensures the imports will work correctly
echo "Copying source files..."
cp -r ../src/palios_taey/models/* src/palios_taey/models/
cp -r ../src/palios_taey/routing/* src/palios_taey/routing/

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
  --set-env-vars="PROJECT_ID=$PROJECT_ID,ENVIRONMENT=dev,COLLECTION_PREFIX=memory_,MODELS_CONFIG_DIR=config/model_capabilities,MIN_CAPABILITY_SCORE=0.7,USE_MOCK_RESPONSES=true"

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
echo "python verify_models.py"
