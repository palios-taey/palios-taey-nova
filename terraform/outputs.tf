# outputs.tf - Terraform outputs for PALIOS-TAEY infrastructure

output "project_id" {
  description = "The project ID that was used"
  value       = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
}

output "firestore_database" {
  description = "The Firestore database ID"
  value       = google_firestore_database.palios_taey_db.name
}

output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.palios_taey_service.status[0].url
}

output "cloud_run_service_id" {
  description = "The fully qualified ID of the Cloud Run service"
  value       = google_cloud_run_service.palios_taey_service.id
}

output "cloud_run_service_account_email" {
  description = "The service account email for Cloud Run"
  value       = google_service_account.cloud_run_service_account.email
}

output "api_gateway_endpoint" {
  description = "The API Gateway endpoint"
  value       = var.use_api_gateway ? google_api_gateway_gateway.api_gateway[0].default_hostname : ""
}

output "vpc_network_id" {
  description = "The ID of the VPC network"
  value       = google_compute_network.vpc_network.id
}

output "subnet_id" {
  description = "The ID of the subnet"
  value       = google_compute_subnetwork.subnet.id
}

output "artifact_registry_id" {
  description = "The ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.palios_taey_repo.id
}

output "artifact_registry_url" {
  description = "The URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.palios_taey_repo.name}"
}