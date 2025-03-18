# PALIOS-TAEY Deployment Documentation

## Cloud Infrastructure
- Project: palios-taey-dev
- Region: us-central1
- Components:
  - Firestore Database (Native mode)
  - Cloud Run Service
  - Artifact Registry

## Deployment Process
1. Build container: `gcloud builds submit`
2. Deploy to Cloud Run: `gcloud run deploy`
3. Verify deployment: Access health endpoint

## Configuration
- Environment variables:
  - PROJECT_ID: GCP project ID
  - ENVIRONMENT: Deployment environment (dev, staging, prod)

## Monitoring
- Cloud Run provides built-in monitoring
- Health endpoint: [SERVICE_URL]/health

## Scaling
- Min instances: 1
- Max instances: 10
- CPU: 1
- Memory: 512Mi

## Maintenance
- Redeploy after code changes
- Monitor Firestore usage and quotas
- Review Cloud Run logs for errors
