# iam.tf - IAM roles and permissions for PALIOS-TAEY infrastructure

# Create service account for developers
resource "google_service_account" "developer_service_account" {
  account_id   = "palios-taey-developer-sa"
  display_name = "PALIOS-TAEY Developer Service Account"
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  description = "Service account for developers working on PALIOS-TAEY"
}

# Grant developer service account necessary roles
resource "google_project_iam_member" "developer_roles" {
  for_each = toset([
    "roles/editor",
    "roles/cloudrun.developer",
    "roles/firestore.user",
    "roles/secretmanager.secretAccessor",
    "roles/logging.viewer",
    "roles/monitoring.viewer",
    "roles/artifactregistry.writer"
  ])
  
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.developer_service_account.email}"
  
  depends_on = [google_service_account.developer_service_account]
}

# Create service account for CI/CD pipelines
resource "google_service_account" "cicd_service_account" {
  account_id   = "palios-taey-cicd-sa"
  display_name = "PALIOS-TAEY CI/CD Service Account"
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  description = "Service account for CI/CD pipelines to deploy PALIOS-TAEY"
}

# Grant CI/CD service account necessary roles
resource "google_project_iam_member" "cicd_roles" {
  for_each = toset([
    "roles/cloudbuild.builds.builder",
    "roles/cloudrun.developer",
    "roles/artifactregistry.writer",
    "roles/storage.objectAdmin",
    "roles/iam.serviceAccountUser"
  ])
  
	project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cicd_service_account.email}"
  
  depends_on = [google_service_account.cicd_service_account]
}

# Create custom role for application monitoring
resource "google_project_iam_custom_role" "monitoring_role" {
  project     = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role_id     = "paliostaeycustommonitoringrole"
  title       = "PALIOS-TAEY Monitoring Custom Role"
  description = "Custom role for PALIOS-TAEY monitoring"
  permissions = [
    "monitoring.timeSeries.list",
    "monitoring.timeSeries.create",
    "logging.logEntries.create",
    "logging.logEntries.list",
    "logging.views.access",
    "cloudtrace.traces.patch",
    "cloudtrace.traces.list"
  ]
}

# Create service account for monitoring
resource "google_service_account" "monitoring_service_account" {
  account_id   = "palios-taey-monitoring-sa"
  display_name = "PALIOS-TAEY Monitoring Service Account"
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  description = "Service account for monitoring PALIOS-TAEY"
}

# Grant monitoring service account roles
resource "google_project_iam_member" "monitoring_roles" {
  for_each = toset([
    "roles/monitoring.viewer",
    "roles/logging.viewer",
    "projects/${var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id}/roles/${google_project_iam_custom_role.monitoring_role.role_id}"
  ])
  
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.monitoring_service_account.email}"
  
  depends_on = [
    google_service_account.monitoring_service_account,
    google_project_iam_custom_role.monitoring_role
  ]
}

# Create service account for administrators
resource "google_service_account" "admin_service_account" {
  account_id   = "palios-taey-admin-sa"
  display_name = "PALIOS-TAEY Admin Service Account"
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  description = "Service account for administrators of PALIOS-TAEY"
}

# Grant admin service account roles
resource "google_project_iam_member" "admin_roles" {
  for_each = toset([
    "roles/owner",
    "roles/secretmanager.admin",
    "roles/iam.securityAdmin",
    "roles/cloudrun.admin",
    "roles/firestore.admin"
  ])
  
  project = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.admin_service_account.email}"
  
  depends_on = [google_service_account.admin_service_account]
}

# Create API key for API Gateway (stored in Secret Manager)
resource "google_secret_manager_secret" "api_key_secret" {
  project   = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  secret_id = "palios-taey-api-key"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Create a random API key
resource "random_password" "api_key" {
  length  = 32
  special = false
}

# Store the API key in Secret Manager
resource "google_secret_manager_secret_version" "api_key_version" {
  secret      = google_secret_manager_secret.api_key_secret.id
  secret_data = random_password.api_key.result
  
  depends_on = [google_secret_manager_secret.api_key_secret]
}