#!/bin/bash
# deploy_direct.sh - Deploy directly to Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID=${PROJECT_ID:-"palios-taey-dev"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"palios-taey-service"}

# Display configuration
echo "Deploying PALIOS-TAEY directly to Cloud Run:"
echo "  Project ID:   $PROJECT_ID"
echo "  Region:       $REGION"
echo "  Service Name: $SERVICE_NAME"
echo ""

# Ensure gcloud is set to the correct project
echo "Setting gcloud project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,ENVIRONMENT=dev,USE_MOCK_RESPONSES=true"

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
