# PALIOS-TAEY Infrastructure Documentation

This document describes the Google Cloud Platform (GCP) infrastructure for the PALIOS-TAEY system. The infrastructure is fully managed using Terraform for infrastructure as code.

## Architecture Overview

The PALIOS-TAEY infrastructure consists of the following components:
┌───────────────────────────────────────────────────────────────────────────────────┐
│                            PALIOS-TAEY Infrastructure                              │
│                                                                                   │
│   ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────────┐    │
│   │  API Gateway    │    │   Cloud Run      │    │      Firestore            │    │
│   │                 │    │                  │    │                           │    │
│   │   Secure API    │───▶│  PALIOS-TAEY     │───▶│   Memory System Storage   │    │
│   │    Endpoint     │    │    Service       │    │                           │    │
│   └─────────────────┘    └──────────────────┘    └───────────────────────────┘    │
│           │                       │                           │                    │
│           │                       │                           │                    │
│           ▼                       ▼                           ▼                    │
│   ┌─────────────────────────────────────────────────────────────────────────┐     │
│   │                           VPC Network                                   │     │
│   │                                                                         │     │
│   │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │     │
│   │   │  VPC Connector  │    │  Cloud NAT      │    │  Security       │     │     │
│   │   │                 │    │                 │    │  Firewall       │     │     │
│   │   └─────────────────┘    └─────────────────┘    └─────────────────┘     │     │
│   └─────────────────────────────────────────────────────────────────────────┘     │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐     │
│   │                        IAM & Security                                   │     │
│   │                                                                         │     │
│   │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │     │
│   │   │  Service        │    │  Custom         │    │  Secret         │     │     │
│   │   │  Accounts       │    │  Roles          │    │  Manager        │     │     │
│   │   └─────────────────┘    └─────────────────┘    └─────────────────┘     │     │
│   └─────────────────────────────────────────────────────────────────────────┘     │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
Copy
## Infrastructure Components

### 1. Google Cloud Project

The infrastructure is deployed within a GCP project specifically created for PALIOS-TAEY. The project is configured with the necessary APIs and services enabled.

**APIs Enabled:**
- Cloud Resource Manager
- Service Usage
- IAM
- Firestore
- Cloud Run
- API Gateway
- Artifact Registry
- Compute Engine (for VPC)
- Service Networking
- Logging and Monitoring
- Secret Manager

### 2. Firestore Database

A Firestore database in native mode serves as the storage backend for the PALIOS-TAEY Memory System.

**Key Features:**
- Native mode for real-time updates
- Point-in-time recovery enabled
- Initial configuration for Memory System tiers
- Default context for general use
- Transcript context for transcript analysis

### 3. Cloud Run Service

The PALIOS-TAEY application is deployed as a containerized service on Cloud Run.

**Key Features:**
- Autoscaling from 0 to 10 instances
- VPC connectivity via VPC Access Connector
- Custom service account with least privilege
- CPU and memory limits configured for optimal performance
- Environment variables for configuration

### 4. API Gateway

An API Gateway provides a secure, managed API endpoint for external access to PALIOS-TAEY services.

**Key Features:**
- OpenAPI specification for routing
- Path-based routing to Cloud Run service
- Custom domain support
- API key authentication
- Secure service account for backend access

### 5. VPC Network

A private Virtual Private Cloud (VPC) network provides secure networking for the infrastructure.

**Key Features:**
- Custom subnet for Cloud Run
- VPC Access Connector for serverless services
- Cloud NAT for outbound connectivity
- Firewall rules for security
- Flow logs for monitoring and troubleshooting

### 6. IAM & Security

Comprehensive Identity and Access Management (IAM) ensures secure access to resources.

**Key Features:**
- Service accounts with least privilege
- Custom roles for specific needs
- Secret Manager for API keys and sensitive data
- Granular permissions for different user roles (developers, admins, CI/CD)

### 7. Artifact Registry

A Docker repository for storing container images.

**Key Features:**
- Regional repository
- IAM integration for access control
- Used by Cloud Run and CI/CD pipelines

## Deployment Instructions

### Prerequisites

1. Google Cloud SDK installed and configured
2. Terraform installed (v1.0.0+)
3. Access to a GCP project or organization

### Deploying the Infrastructure

Use the provided `apply_infrastructure.sh` script to deploy the infrastructure:

```bash
# For an existing project
./scripts/apply_infrastructure.sh --project-id=your-project-id --environment=dev

# For creating a new project
./scripts/apply_infrastructure.sh --create-project=true --org-id=your-org-id --billing-account=your-billing-account --environment=dev