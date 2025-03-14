# variables.tf - Variable definitions for PALIOS-TAEY infrastructure

variable "project_id" {
  description = "The GCP project ID to deploy resources"
  type        = string
}

variable "project_name" {
  description = "The display name of the GCP project"
  type        = string
  default     = "PALIOS-TAEY"
}

variable "create_project" {
  description = "Whether to create the project or use an existing one"
  type        = bool
  default     = false
}

variable "org_id" {
  description = "The GCP organization ID (required if create_project is true)"
  type        = string
  default     = ""
}

variable "billing_account" {
  description = "The GCP billing account ID (required if create_project is true)"
  type        = string
  default     = ""
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "palios-taey-network"
}

variable "subnet_name" {
  description = "Name of the subnet for Cloud Run"
  type        = string
  default     = "palios-taey-subnet"
}

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "firestore_location" {
  description = "Location for Firestore database"
  type        = string
  default     = "us-central"
}

variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "palios-taey-service"
}

variable "cloud_run_service_account_name" {
  description = "Name of the service account for Cloud Run"
  type        = string
  default     = "palios-taey-cloudrun-sa"
}

variable "api_gateway_name" {
  description = "Name of the API Gateway"
  type        = string
  default     = "palios-taey-api-gateway"
}

variable "api_config_name" {
  description = "Name of the API Gateway configuration"
  type        = string
  default     = "palios-taey-api-config"
}

variable "api_id" {
  description = "ID for the API Gateway API"
  type        = string
  default     = "palios-taey-api"
}

variable "container_image" {
  description = "Default placeholder container image for Cloud Run"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "min_instance_count" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instance_count" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "512Mi"
}

variable "artifact_registry_name" {
  description = "Name of the Artifact Registry repository"
  type        = string
  default     = "palios-taey-repo"
}