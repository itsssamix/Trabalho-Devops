terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.region
}

resource "google_container_cluster" "pedidos_veloz_cluster" {
  name     = "pedidos-veloz-cluster"
  location = var.region

  initial_node_count = 1

  node_config {
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.pedidos_veloz_cluster.name
}

output "cluster_endpoint" {
  value = google_container_cluster.pedidos_veloz_cluster.endpoint
}