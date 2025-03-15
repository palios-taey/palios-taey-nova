# Immediate Deployment Action Plan

## Priority 1: Manual Firestore Setup
1. Navigate to Firestore in GCP Console (https://console.cloud.google.com/firestore)
2. Create database in Native mode with location "us-central"
3. Create initial collections:
   - Collection: "config", Document: "memory_system" with fields as documented
   - Collection: "memory_contexts", Document: "default_context" with fields as documented

## Priority 2: Container Image Creation
1. Clone repository: `git clone https://github.com/palios-taey/palios-taey-nova.git`
2. Create Dockerfile if not exists:
   ```
   cat > Dockerfile <<EOL
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   ENV PORT=8080
   
   CMD exec gunicorn --bind : --workers 1 --threads 8 main:app
   EOL
   ```
3. Create minimal requirements.txt:
   ```
   cat > requirements.txt <<EOL
   flask==2.0.1
   google-cloud-firestore==2.3.4
   gunicorn==20.1.0
   pydantic==1.8.2
   requests==2.26.0
   EOL
   ```
4. Create minimal main.py:
   ```
   cat > main.py <<EOL
   from flask import Flask, jsonify
   
   app = Flask(__name__)
   
   @app.route('/health')
   def health():
       return jsonify({
           "status": "healthy",
           "version": "1.0.0"
       })
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8080)
   EOL
   ```
5. Manual build and push:
   ```
   gcloud builds submit --tag us-central1-docker.pkg.dev/palios-taey-dev/palios-taey/api:latest
   ```

## Priority 3: Cloud Run Deployment
1. Navigate to Cloud Run in GCP Console
2. Deploy container with:
   - Service name: "palios-taey-service"
   - Region: "us-central1"
   - CPU: 1
   - Memory: 512 MiB
   - Min instances: 1
   - Environment variables:
     - PROJECT_ID: "palios-taey-dev"
     - ENVIRONMENT: "dev"
3. Configure service account with necessary permissions

## Priority 4: Basic API Integration
1. Document Cloud Run URL
2. Create basic API integration documentation
3. Test health endpoint functionality

## Priority 5: Deployment Documentation
1. Document all manual steps taken
2. Create troubleshooting guide based on encountered issues
3. Prepare knowledge transfer documentation
