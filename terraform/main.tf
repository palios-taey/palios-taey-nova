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
    bucket = "palios-taey-terraform-state"
    prefix = "terraform/state"
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

# Configure project metadata for organization info
resource "google_compute_project_metadata_item" "project_metadata" {
  project = var.project_id
  key     = "palios-taey-infrastructure-version"
  value   = "1.0.0"
}

# Set up resource locations and defaults
resource "google_project_default_service_accounts" "default" {
  project = var.project_id
  action  = "DISABLE"
}
