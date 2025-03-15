# PALIOS-TAEY Deployment Process

## Overview
This document outlines the complete process for deploying the PALIOS-TAEY system to Google Cloud Platform using our hybrid approach. It includes both manual and automated steps with detailed instructions for each.

## 1. GCP Setup (Manual)

### 1.1 Organization and Project Creation
1. Log into Google Cloud Console: https://console.cloud.google.com/
2. Create or select an organization
3. Create a new project:
   - Name: PALIOS-TAEY-[ENV]
   - Organization: [Your Organization]
4. Link billing account to project

### 1.2 API Enablement
Enable the following APIs through Google Cloud Console or gcloud:
- Cloud Resource Manager API
- Service Usage API
- Identity and Access Management API
- Firestore API
- Cloud Run API
- API Gateway API
- Artifact Registry API
- Compute Engine API
- Service Networking API
- Cloud Logging API
- Cloud Monitoring API
- Cloud Trace API
- Secret Manager API

Command to enable all APIs:
```bash
gcloud services enable cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  iam.googleapis.com \
  firestore.googleapis.com \
  run.googleapis.com \
  apigateway.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  secretmanager.googleapis.com \
  --project=[PROJECT_ID]
```

### 1.3 Terraform State Storage
Create a Cloud Storage bucket for Terraform state:
```bash
gsutil mb -p [PROJECT_ID] -l us-central1 gs://[PROJECT_ID]-terraform-state
gsutil versioning set on gs://[PROJECT_ID]-terraform-state
```

### 1.4 Authentication Setup
Configure authentication for deployment:
```bash
gcloud auth login
gcloud config set project [PROJECT_ID]
```

## 2. Infrastructure Deployment (Hybrid)

### 2.1 Terraform Initialization
```bash
cd terraform
terraform init -backend-config="bucket=[PROJECT_ID]-terraform-state"
```

### 2.2 Firestore Deployment
```bash
terraform plan -target=google_firestore_database.palios_taey_db
terraform apply -target=google_firestore_database.palios_taey_db
```

Verify in GCP Console: https://console.cloud.google.com/firestore

### 2.3 Service Account Creation
```bash
terraform plan -target=google_service_account.cloud_run_service_account
terraform apply -target=google_service_account.cloud_run_service_account
```

Verify in GCP Console: https://console.cloud.google.com/iam-admin/serviceaccounts

### 2.4 Artifact Registry Setup
```bash
terraform plan -target=google_artifact_registry_repository.palios_taey_repo
terraform apply -target=google_artifact_registry_repository.palios_taey_repo
```

Verify in GCP Console: https://console.cloud.google.com/artifacts

### 2.5 Cloud Run Configuration
```bash
terraform plan -target=google_cloud_run_service.palios_taey_service
terraform apply -target=google_cloud_run_service.palios_taey_service
```

Verify in GCP Console: https://console.cloud.google.com/run

## 3. Application Deployment

### 3.1 Container Build and Push
```bash
./scripts/build_push.sh [PROJECT_ID] palios-taey latest
```

### 3.2 Deploy to Cloud Run
Update the container image in Cloud Run:
```bash
terraform apply -var="container_image=us-central1-docker.pkg.dev/[PROJECT_ID]/palios-taey/palios-taey:latest"
```

### 3.3 Verify Deployment
Test the deployment:
```bash
curl $(gcloud run services describe palios-taey-service --format='value(status.url)')/health
```

Expected output: 
```json
{"status": "healthy", "version": "1.0.0"}
```

## 4. Configuration

### 4.1 Environment Variables
Configure environment variables through Terraform or Google Cloud Console:
- PROJECT_ID: GCP project ID
- ENVIRONMENT: Development environment (dev, staging, prod)

### 4.2 API Integrations
Configure API integrations through configuration files:
- Claude API
- Grok Think/DeepSearch

### 4.3 Security Configuration
Set up security:
- API key authentication
- Service account permissions

## 5. Monitoring and Maintenance

### 5.1 Logging Setup
View logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=palios-taey-service" --project=[PROJECT_ID]
```

### 5.2 Monitoring
Set up monitoring through Google Cloud Console:
- CPU utilization
- Memory usage
- Request latency

### 5.3 Maintenance Tasks
Regular maintenance tasks:
- Update dependencies
- Rotate API keys
- Review performance metrics

## 6. Troubleshooting

### 6.1 Deployment Issues
If deployment fails:
- Check service account permissions
- Verify API enablement
- Check Terraform state
- Examine Cloud Build logs

### 6.2 Runtime Issues
If application fails at runtime:
- Check Cloud Run logs
- Verify environment variables
- Test service connections
- Check Firestore access

## 7. Redeployment

To redeploy after changes:
```bash
# Build and push new container
./scripts/build_push.sh [PROJECT_ID] palios-taey [NEW_TAG]

# Update Cloud Run service
terraform apply -var="container_image=us-central1-docker.pkg.dev/[PROJECT_ID]/palios-taey/palios-taey:[NEW_TAG]"
```
