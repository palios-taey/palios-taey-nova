#!/bin/bash
set -e

# PALIOS-TAEY hybrid deployment script
# This script provides options for both local and cloud deployment

# Configuration
PROJECT_ID="palios-taey-dev"
REGION="us-central1"
SERVICE_NAME="palios-taey"
ARTIFACT_REPO="palios-taey-repo"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${SERVICE_NAME}"

# Display help
show_help() {
  echo "PALIOS-TAEY Deployment"
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -m, --mode MODE       Deployment mode (local, docker, cloud) [default: local]"
  echo "  -p, --port PORT       Port to use for local deployment [default: 8080]"
  echo "  -h, --help            Show this help message"
  exit 1
}

# Default values
MODE="local"
PORT="8080"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--mode)
      MODE="$2"
      shift 2
      ;;
    -p|--port)
      PORT="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      ;;
  esac
done

# Validate mode
if [[ ! "$MODE" =~ ^(local|docker|cloud)$ ]]; then
  echo "Error: Mode must be one of: local, docker, cloud"
  exit 1
fi

# Run environment fix script
echo "Fixing environment configuration..."
./fix_environment_config.sh

# Deploy based on mode
if [ "$MODE" = "local" ]; then
  echo "===== Local Deployment ====="
  
  # Create virtual environment if it doesn't exist
  if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
  fi
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install requirements
  pip install -r requirements.txt
  
  # Set environment variables
  export USE_MOCK_RESPONSES=true
  export ENVIRONMENT=development
  export PORT=$PORT
  
  echo "Starting application locally on port $PORT..."
  cd src
  python -m flask run --host=0.0.0.0 --port=$PORT
  
elif [ "$MODE" = "docker" ]; then
  echo "===== Docker Deployment ====="
  
  # Build Docker image
  echo "Building Docker image..."
  docker build -t palios-taey:latest .
  
  # Run container
  echo "Running container on port $PORT..."
  docker run -p $PORT:8080 \
    -e USE_MOCK_RESPONSES=true \
    -e ENVIRONMENT=development \
    -e PORT=8080 \
    palios-taey:latest
  
elif [ "$MODE" = "cloud" ]; then
  echo "===== Cloud Deployment ====="
  
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
  fi
  
  # Use Cloud Build
  echo "Building and pushing with Cloud Build..."
  gcloud builds submit --tag=${IMAGE_NAME} .
  
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
    --update-env-vars "PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production,USE_MOCK_RESPONSES=true"
  
  # Display deployed service URL
  SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
  echo "Service URL: ${SERVICE_URL}"
  echo "Health Check: ${SERVICE_URL}/health"
fi
