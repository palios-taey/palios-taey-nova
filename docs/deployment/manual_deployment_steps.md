# Manual Deployment Steps

## 1. Authentication Setup
1. Login to Google Cloud Console (https://console.cloud.google.com/)
2. Select project "palios-taey-dev"
3. Open Cloud Shell

## 2. Firestore Setup
1. Navigate to Firestore in the GCP Console
2. Click "Create Database"
3. Select "Native Mode"
4. Choose location "us-central"
5. Wait for database creation to complete
6. Create collection "config" with document "memory_system"
7. Add the following fields to the document:
   - version: string = "1.0.0"
   - initial_setup: boolean = true
   - Add map field "tiers" containing:
     - ephemeral: map with field ttl_days: number = 0.5
     - working: map with field ttl_days: number = 14.0
     - reference: map with field ttl_days: number = 180.0
     - archival: map with field ttl_days: null

## 3. Service Account Creation
1. Navigate to IAM & Admin > Service Accounts
2. Click "Create Service Account"
3. Name: "palios-taey-cloudrun-sa"
4. Description: "Service account for PALIOS-TAEY Cloud Run"
5. Click "Create and Continue"
6. Add the following roles:
   - Cloud Datastore User
   - Secret Manager Secret Accessor
7. Click "Done"

## 4. Artifact Registry Setup
1. Navigate to Artifact Registry
2. Click "Create Repository"
3. Name: "palios-taey"
4. Format: "Docker"
5. Location type: "Region"
6. Region: "us-central1"
7. Click "Create"

## 5. Build and Push Docker Image
1. In Cloud Shell, clone the application repository:
   ```
   git clone https://github.com/palios-taey/palios-taey-nova.git
   cd palios-taey-nova
   ```
2. Build the Docker image:
   ```
   gcloud builds submit --tag us-central1-docker.pkg.dev/palios-taey-dev/palios-taey/api:latest
   ```

## 6. Cloud Run Deployment
1. Navigate to Cloud Run in the GCP Console
2. Click "Create Service"
3. Select "Deploy one revision from an existing container image"
4. Click "Browse" and select the image from Artifact Registry
5. Set service name: "palios-taey-service"
6. Set region: "us-central1"
7. Authentication: "Allow unauthenticated invocations"
8. Click "Container, Networking, Security" to expand
9. Set CPU allocation: "1 CPU"
10. Set memory allocation: "512 MiB"
11. Set minimum instances: "1"
12. Set maximum instances: "10" 
13. Add environment variables:
    - PROJECT_ID: "palios-taey-dev"
    - ENVIRONMENT: "dev"
14. Under "Service account", select the previously created account
15. Click "Create"

## 7. Verify Deployment
1. After deployment completes, click the URL provided for the Cloud Run service
2. Add "/health" to the URL to check the health endpoint
3. Verify you receive a successful response

## 8. API Access Documentation
1. Document the Cloud Run URL for future API integration
2. Note any authentication requirements for API access
3. Document environment variables needed for client applications
