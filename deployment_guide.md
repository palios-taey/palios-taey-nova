# PALIOS-TAEY Deployment Guide

This guide provides instructions for deploying and testing the PALIOS-TAEY platform.

## Deployment Steps

1. Ensure all files are in the correct locations:
   - `src/environment_config.py`
   - `src/main.py`
   - `src/palios_taey/protocols/manager.py`
   - `src/palios_taey/protocols/__init__.py`
   - `src/palios_taey/models/protocol_capabilities.py`
   - `src/palios_taey/models/registry_protocol_integration.py`
   - `src/palios_taey/routing/protocol_router.py`
   - `src/palios_taey/transcripts/protocol_integration.py`
   - `Dockerfile`
   - `requirements.txt`
   - `deploy.sh`

2. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh

Run the deployment script:
bashCopy./deploy.sh

Wait for the deployment to complete. The script will output the service URL once done.

Testing Steps

Make the test script executable:
bashCopychmod +x test_deployment.sh

Run the test script:
bashCopy./test_deployment.sh

For more comprehensive testing, use the integration test script:
bashCopypython integration_test.py --base-url YOUR_SERVICE_URL


Verification
After deploying, verify the following:

Health Check: Visit the health endpoint at YOUR_SERVICE_URL/health
API Endpoints: Check each API endpoint:

Memory: YOUR_SERVICE_URL/api/memory
Models: YOUR_SERVICE_URL/api/models
Tasks: YOUR_SERVICE_URL/api/tasks
Routing: YOUR_SERVICE_URL/api/route
Transcripts: YOUR_SERVICE_URL/api/transcripts
Protocols: YOUR_SERVICE_URL/api/protocols


Documentation: Access the API documentation at YOUR_SERVICE_URL/docs

Troubleshooting
If you encounter issues during deployment or testing:

Check the logs:
bashCopygcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=palios-taey" --limit 50

Verify environment variables:
bashCopygcloud run services describe palios-taey --format="yaml(spec.template.spec.containers[0].env)"

Check service status:
bashCopygcloud run services describe palios-taey


