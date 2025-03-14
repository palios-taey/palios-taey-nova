# cloud_run.tf - Cloud Run configuration for PALIOS-TAEY application

# Create a service account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  account_id   = var.cloud_run_service_account_name
  display_name = "PALIOS-TAEY Cloud Run Service Account"
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  description = "Service account for PALIOS-TAEY Cloud Run service with access to Firestore and other GCP services"
  
  depends_on = [google_project_service.required_apis]
}

# Grant the Cloud Run service account access to Firestore
resource "google_project_iam_member" "firestore_access" {
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
  
  depends_on = [google_service_account.cloud_run_service_account]
}

# Grant the Cloud Run service account access to Secret Manager
resource "google_project_iam_member" "secret_manager_access" {
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
  
  depends_on = [google_service_account.cloud_run_service_account]
}

# Create an Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "palios_taey_repo" {
  provider      = google-beta
  project       = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  location      = var.region
  repository_id = var.artifact_registry_name
  description   = "Docker repository for PALIOS-TAEY images"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# Grant the Cloud Run service account access to Artifact Registry
resource "google_artifact_registry_repository_iam_member" "repo_access" {
  provider   = google-beta
  project    = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.palios_taey_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Create a Cloud Run service
resource "google_cloud_run_service" "palios_taey_service" {
  name     = var.cloud_run_service_name
  location = var.region
  project  = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "internal-and-cloud-load-balancing"
    }
    labels = {
      "environment" = var.environment
      "managed-by"  = "terraform"
      "app"         = "palios-taey"
    }
  }
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instance_count
        "autoscaling.knative.dev/maxScale" = var.max_instance_count
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.name
        "run.googleapis.com/vpc-access-egress" = "private-ranges-only"
        "run.googleapis.com/cloudsql-instances" = ""
      }
      labels = {
        "environment" = var.environment
        "managed-by"  = "terraform"
        "app"         = "palios-taey"
      }
    }
    
    spec {
      service_account_name = google_service_account.cloud_run_service_account.email
      
      containers {
        image = var.container_image
        
        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
        }
        
        env {
          name  = "COLLECTION_PREFIX"
          value = var.environment == "prod" ? "" : "${var.environment}_"
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
  
  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.connector,
    google_service_account.cloud_run_service_account
  ]
}

# Allow unauthenticated access to the Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.palios_taey_service.location
  project  = google_cloud_run_service.palios_taey_service.project
  service  = google_cloud_run_service.palios_taey_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}