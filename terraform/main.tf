# main.tf - Main Terraform configuration for PALIOS-TAEY infrastructure

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.80.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.80.0"
    }
  }
  backend "gcs" {
    # This will be configured via the apply_infrastructure.sh script
    # bucket = "palios-taey-terraform-state"
    # prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Create a GCP project if it doesn't exist yet
resource "google_project" "palios_taey_project" {
  count           = var.create_project ? 1 : 0
  name            = var.project_name
  project_id      = var.project_id
  org_id          = var.org_id
  billing_account = var.billing_account
  
  labels = {
    environment = var.environment
    project     = "palios-taey"
    managed-by  = "terraform"
  }
}

# Enable required GCP APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",  # For resource management
    "serviceusage.googleapis.com",          # For API enablement
    "iam.googleapis.com",                   # For IAM
    "firestore.googleapis.com",             # For Firestore
    "run.googleapis.com",                   # For Cloud Run
    "apigateway.googleapis.com",            # For API Gateway
    "artifactregistry.googleapis.com",      # For Docker repositories
    "compute.googleapis.com",               # For VPC
    "servicenetworking.googleapis.com",     # For VPC peering
    "logging.googleapis.com",               # For logging
    "monitoring.googleapis.com",            # For monitoring
    "cloudtrace.googleapis.com",            # For tracing
    "secretmanager.googleapis.com"          # For secrets management
  ])
  
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Configure project metadata for organization info
resource "google_compute_project_metadata_item" "project_metadata" {
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  key     = "palios-taey-infrastructure-version"
  value   = "1.0.0"
  
  depends_on = [google_project_service.required_apis]
}

# Set up resource locations and defaults
resource "google_project_default_service_accounts" "default" {
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  action  = "DISABLE"
  
  depends_on = [google_project_service.required_apis]
}