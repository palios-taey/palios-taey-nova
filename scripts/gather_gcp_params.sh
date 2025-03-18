#!/bin/bash

# Script to gather GCP deployment parameters
# Prerequisites: gcloud CLI installed and authenticated with admin account

# Output file
OUTPUT_FILE="gcp_deployment_parameters.md"

echo "# GCP Deployment Parameters" > $OUTPUT_FILE
echo "Generated on: $(date)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Verify authentication
echo "## Current Authentication" >> $OUTPUT_FILE
gcloud auth list --filter=status:ACTIVE --format="value(account)" > temp.txt
CURRENT_ACCOUNT=$(cat temp.txt)
echo "- **Admin Account**: \`$CURRENT_ACCOUNT\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Organization & Project information
echo "## Organization & Project Identifiers" >> $OUTPUT_FILE
gcloud organizations list --format="value(DISPLAY_NAME,ID)" > temp.txt
if [ -s temp.txt ]; then
  echo "- **Organizations**:" >> $OUTPUT_FILE
  while read line; do
    echo "  - $line" >> $OUTPUT_FILE
  done < temp.txt
else
  echo "- **Organizations**: None accessible" >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Project information
echo "- **Current Project**:" >> $OUTPUT_FILE
gcloud config get-value project > temp.txt
CURRENT_PROJECT=$(cat temp.txt)
echo "  - Name: \`$CURRENT_PROJECT\`" >> $OUTPUT_FILE

# Project number
gcloud projects describe $CURRENT_PROJECT --format="value(projectNumber)" > temp.txt
PROJECT_NUMBER=$(cat temp.txt)
echo "  - Number: \`$PROJECT_NUMBER\`" >> $OUTPUT_FILE

# Default region and zone
echo "" >> $OUTPUT_FILE
echo "- **Default Region**: \`$(gcloud config get-value compute/region)\`" >> $OUTPUT_FILE
echo "- **Default Zone**: \`$(gcloud config get-value compute/zone)\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Service accounts
echo "## Service Accounts" >> $OUTPUT_FILE
gcloud iam service-accounts list --format="table(EMAIL,DISPLAY_NAME)" > temp.txt
echo "\`\`\`" >> $OUTPUT_FILE
cat temp.txt >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Artifact Registry information
echo "## Artifact Registry" >> $OUTPUT_FILE
gcloud artifacts repositories list --format="table(REPOSITORY,FORMAT,LOCATION,ENCRYPTION)" > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
  
  # Extract repository details for each repository
  gcloud artifacts repositories list --format="value(name)" > repos.txt
  if [ -s repos.txt ]; then
    echo "" >> $OUTPUT_FILE
    echo "### Registry Paths" >> $OUTPUT_FILE
    while read repo; do
      repo_name=$(basename $repo)
      region=$(gcloud artifacts repositories describe $repo_name --format="value(location)")
      echo "- \`$region-docker.pkg.dev/$CURRENT_PROJECT/$repo_name\`" >> $OUTPUT_FILE
    done < repos.txt
  fi
else
  echo "No artifact repositories found." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Network information
echo "## Networking" >> $OUTPUT_FILE
echo "### VPC Networks" >> $OUTPUT_FILE
gcloud compute networks list --format="table(NAME,SUBNET_MODE,IPV4_RANGE)" > temp.txt
echo "\`\`\`" >> $OUTPUT_FILE
cat temp.txt >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "### Subnets" >> $OUTPUT_FILE
gcloud compute networks subnets list --format="table(NAME,REGION,NETWORK,RANGE)" > temp.txt
echo "\`\`\`" >> $OUTPUT_FILE
cat temp.txt >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Firewall rules (limited to 10 to avoid excessive output)
echo "### Firewall Rules (Top 10)" >> $OUTPUT_FILE
gcloud compute firewall-rules list --limit=10 --format="table(NAME,NETWORK,DIRECTION,PRIORITY,ALLOW)" > temp.txt
echo "\`\`\`" >> $OUTPUT_FILE
cat temp.txt >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Load balancers
echo "### Load Balancers" >> $OUTPUT_FILE
gcloud compute forwarding-rules list --format="table(NAME,REGION,IP_ADDRESS,IP_PROTOCOL,TARGET)" > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
else
  echo "No forwarding rules found." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Cloud Run services
echo "## Cloud Run Services" >> $OUTPUT_FILE
gcloud run services list --format="table(SERVICE,REGION,URL,LAST_DEPLOYED_TIME)" > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
else
  echo "No Cloud Run services found." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# GKE clusters
echo "## GKE Clusters" >> $OUTPUT_FILE
gcloud container clusters list --format="table(NAME,LOCATION,MASTER_VERSION,MASTER_IP,MACHINE_TYPE,NODE_VERSION,NUM_NODES,STATUS)" > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
else
  echo "No GKE clusters found." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Database instances
echo "## Database Instances" >> $OUTPUT_FILE
echo "### Cloud SQL" >> $OUTPUT_FILE
gcloud sql instances list --format="table(NAME,DATABASE_VERSION,LOCATION,TIER,PRIMARY_ADDRESS,STATUS)" > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
else
  echo "No Cloud SQL instances found." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Storage buckets
echo "## Storage Buckets" >> $OUTPUT_FILE
gsutil ls > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
else
  echo "No storage buckets found or accessible." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Secret Manager secrets (without values)
echo "## Secret Manager Secrets" >> $OUTPUT_FILE
gcloud secrets list --format="table(NAME,CREATED_AT)" > temp.txt
if [ -s temp.txt ]; then
  echo "\`\`\`" >> $OUTPUT_FILE
  cat temp.txt >> $OUTPUT_FILE
  echo "\`\`\`" >> $OUTPUT_FILE
else
  echo "No secrets found or accessible." >> $OUTPUT_FILE
fi
echo "" >> $OUTPUT_FILE

# Cleanup
rm temp.txt
if [ -f repos.txt ]; then
  rm repos.txt
fi

echo "GCP deployment parameters gathered successfully in $OUTPUT_FILE"