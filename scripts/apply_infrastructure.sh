#!/bin/bash
# apply_infrastructure.sh - Script to apply Terraform configuration for PALIOS-TAEY infrastructure

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"palios-taey-${ENVIRONMENT:-dev}"}
REGION=${REGION:-"us-central1"}
ENVIRONMENT=${ENVIRONMENT:-"dev"}
CREATE_PROJECT=${CREATE_PROJECT:-"false"}
ORG_ID=${ORG_ID:-""}
BILLING_ACCOUNT=${BILLING_ACCOUNT:-""}

# Helper function to display usage information
function show_usage {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project-id       The GCP project ID to deploy resources (default: palios-taey-{ENVIRONMENT})"
  echo "  -r, --region           The GCP region for resources (default: us-central1)"
  echo "  -e, --environment      The environment (dev, staging, prod) (default: dev)"
  echo "  -c, --create-project   Whether to create a new project (true/false) (default: false)"
  echo "  -o, --org-id           The GCP organization ID (required if create-project is true)"
  echo "  -b, --billing-account  The GCP billing account ID (required if create-project is true)"
  echo "  -h, --help             Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    -r|--region)
      REGION="$2"
      shift 2
      ;;
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -c|--create-project)
      CREATE_PROJECT="$2"
      shift 2
      ;;
    -o|--org-id)
      ORG_ID="$2"
      shift 2
      ;;
    -b|--billing-account)
      BILLING_ACCOUNT="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      exit 1
      ;;
  esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
  echo "Error: Environment must be one of: dev, staging, prod"
  exit 1
fi

# Validate project creation requirements
if [[ "$CREATE_PROJECT" == "true" ]]; then
  if [[ -z "$ORG_ID" || -z "$BILLING_ACCOUNT" ]]; then
    echo "Error: When creating a new project, both org-id and billing-account are required"
    exit 1
  fi
fi

# Change to the Terraform directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform"
cd "$TERRAFORM_DIR"

echo "Initializing Terraform..."

# Check if we're creating a new project
if [[ "$CREATE_PROJECT" == "true" ]]; then
  # For new projects, initialize Terraform locally first
  terraform init
else
  # For existing projects, check if a GCS bucket for state exists and create if needed
  GCS_BUCKET="palios-taey-terraform-state-${PROJECT_ID}"
  
  if ! gsutil ls -b "gs://${GCS_BUCKET}" &>/dev/null; then
    echo "Creating GCS bucket for Terraform state..."
    gsutil mb -l "$REGION" "gs://${GCS_BUCKET}"
    gsutil versioning set on "gs://${GCS_BUCKET}"
    gsutil lifecycle set - <<EOF > /dev/null 2>&1
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "numNewerVersions": 10,
        "isLive": false
      }
    }
  ]
}
EOF
  fi
  
  # Initialize Terraform with GCS backend
  terraform init -backend-config="bucket=${GCS_BUCKET}" -backend-config="prefix=terraform/state"
fi

# Create a tfvars file
cat > terraform.tfvars <<EOF
project_id        = "${PROJECT_ID}"
project_name      = "PALIOS-TAEY-${ENVIRONMENT}"
create_project    = ${CREATE_PROJECT}
org_id            = "${ORG_ID}"
billing_account   = "${BILLING_ACCOUNT}"
region            = "${REGION}"
zone              = "${REGION}-a"
environment       = "${ENVIRONMENT}"
EOF

# Apply the Terraform configuration
echo "Planning Terraform changes..."
terraform plan -var-file=terraform.tfvars -out=tfplan

echo "Applying Terraform configuration..."
terraform apply tfplan

echo "Infrastructure deployment complete!"

# Display important outputs
echo ""
echo "Infrastructure Details:"
echo "----------------------"
terraform output

exit 0