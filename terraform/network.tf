# network.tf - Network configuration for PALIOS-TAEY infrastructure

# Create a VPC network
resource "google_compute_network" "vpc_network" {
  project                 = var.project_id
  name                    = var.network_name
  auto_create_subnetworks = false
  mtu                     = 1500
  routing_mode            = "REGIONAL"
}

# Create a subnet for Cloud Run services
resource "google_compute_subnetwork" "subnet" {
  project       = var.project_id
  name          = var.subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc_network.id
  
  private_ip_google_access = true
  
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Create a serverless VPC access connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "palios-taey-vpc-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc_network.name
  project       = var.project_id
}
