CLAUDE_PROTOCOL_V1.0:MTD{
  "protocol_version": "1.0",
  "document_type": "DEPLOYMENT_GUIDE",
  "critical_level": "HIGH",
  "verification_status": "TEMPLATE",
  "implementation_stage": "IMMEDIATE",
  "application_scope": "PRODUCTION_DEPLOYMENT",
  "associated_framework": "SIX_SIGMA_QUALITY",
  "required_components": [
    "CORE", "MEMORY", "MODELS",
    "ROUTING", "TASKS", "TRANSCRIPTS", "API"
  ],
  "deployment_environment": "GCP",
  "verification_required": true
}

# PALIOS-TAEY Deployment Guide

**VERIFICATION_STRING:** NOVA_DEPLOYMENT_PHASE1_20250317
**LAST_UPDATED:** 2025-03-17
**DOCUMENT_PURPOSE:** Complete GCP deployment instructions

## Deployment Overview

This guide provides comprehensive instructions for deploying the PALIOS-TAEY system to Google Cloud Platform. The deployment process follows an incremental approach with verification at each step to ensure reliability and functionality.

# PALIOS-TAEY Deployment Guide

## Prerequisites
- Google Cloud Platform account with billing enabled
- Project with required APIs enabled:
  - Cloud Run
  - Firestore
  - Artifact Registry
  - Cloud Build
- gcloud CLI installed and configured

## Deployment Steps

### 1. Clone the Repository
\`\`\`bash
git clone https://github.com/your-org/palios-taey.git
cd palios-taey
\`\`\`

### 2. Set Up Firestore
1. Navigate to Firestore in GCP Console
2. Create a database in Native mode
3. Choose location: us-central
4. Wait for database creation to complete

### 3. Configure Authentication
\`\`\`bash
# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project palios-taey-dev
\`\`\`

### 4. Build and Deploy
\`\`\`bash
# Create Artifact Registry repository
gcloud artifacts repositories create palios-taey \\
  --repository-format=docker \\
  --location=us-central1

# Build and push container
gcloud builds submit --tag us-central1-docker.pkg.dev/palios-taey-dev/palios-taey/api:latest

# Deploy to Cloud Run
gcloud run deploy palios-taey-service \\
  --image us-central1-docker.pkg.dev/palios-taey-dev/palios-taey/api:latest \\
  --platform managed \\
  --region us-central1 \\
  --allow-unauthenticated \\
  --memory 512Mi \\
  --cpu 1 \\
  --set-env-vars="PROJECT_ID=palios-taey-dev,ENVIRONMENT=dev"
\`\`\`

### 5. Verify Deployment
\`\`\`bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe palios-taey-service --format='value(status.url)')

# Check health endpoint
curl $SERVICE_URL/health

# Open dashboard in browser
echo "Open this URL in your browser: $SERVICE_URL"
\`\`\`

## Post-Deployment Configuration

### API Integration

To integrate with Claude API:
1. Set the CLAUDE_API_KEY environment variable
2. Update the Claude model implementation in model_integration.py

To integrate with Grok/DeepSearch:
1. Set the GROK_API_KEY environment variable
2. Update the Grok model implementation in model_integration.py

### Security Configuration

For production, replace the test API key with a securely generated key:
1. Edit the auth.py file
2. Replace the API_KEYS dictionary with secure keys
3. Consider using Secret Manager for key storage

## Maintenance

### Updating the Application
\`\`\`bash
# Build and push new container version
gcloud builds submit --tag us-central1-docker.pkg.dev/palios-taey-dev/palios-taey/api:v2

# Update the deployment
gcloud run deploy palios-taey-service \\
  --image us-central1-docker.pkg.dev/palios-taey-dev/palios-taey/api:v2
\`\`\`

### Monitoring
- Cloud Run provides built-in monitoring
- View logs in Cloud Logging
- Set up alerts for critical metrics

### Troubleshooting

Common issues:
1. **Authentication Errors**: Check API keys and permissions
2. **Firestore Connection**: Verify permissions and indexes
3. **Model Integration**: Check API keys and endpoint URLs

VERIFICATION_CONFIRMATION: NOVA_DEPLOYMENT_PHASE1_20250317
