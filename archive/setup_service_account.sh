#!/bin/bash
set -e

# Configuration
PROJECT_ID="palios-taey-dev"
SERVICE_NAME="palios-taey"

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe ${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
  echo "Creating service account..."
  gcloud iam service-accounts create ${SERVICE_NAME} \
    --display-name="PALIOS-TAEY Service Account"
else
  echo "Service account already exists."
fi

# Grant necessary permissions
echo "Granting permissions..."

# Firestore access
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Storage access
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Secret Manager access
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run invoker
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

echo "Service account configured with all necessary permissions."
