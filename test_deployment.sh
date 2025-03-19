#!/bin/bash
set -e

# Test the PALIOS-TAEY deployment
# This script tests the deployed application

# Get the service URL from gcloud
SERVICE_URL=$(gcloud run services describe palios-taey --region=us-central1 --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
  echo "Error: Could not get service URL. Check that the service is deployed."
  exit 1
fi

echo "Testing PALIOS-TAEY deployment at $SERVICE_URL"

# Test health endpoint
echo "Testing health endpoint..."
curl -s $SERVICE_URL/health

# Test root endpoint
echo -e "\n\nTesting root endpoint..."
curl -s $SERVICE_URL

echo -e "\n\nTests completed successfully!"
