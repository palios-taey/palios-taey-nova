# api_gateway.tf - API Gateway configuration for PALIOS-TAEY external access

# Create a service account for API Gateway
resource "google_service_account" "api_gateway_service_account" {
  account_id   = "palios-taey-api-gateway-sa"
  display_name = "PALIOS-TAEY API Gateway Service Account"
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  
  description = "Service account for PALIOS-TAEY API Gateway with access to Cloud Run service"
}

# Grant the API Gateway service account access to invoke Cloud Run
resource "google_cloud_run_service_iam_member" "api_gateway_run_invoker" {
  location = google_cloud_run_service.palios_taey_service.location
  project  = google_cloud_run_service.palios_taey_service.project
  service  = google_cloud_run_service.palios_taey_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api_gateway_service_account.email}"
}

# Create an API Gateway API
resource "google_api_gateway_api" "api" {
  count    = var.use_api_gateway ? 1 : 0
  provider = google-beta
  project  = var.project_id
  api_id   = var.api_id
}

# Create a basic OpenAPI specification for the API Gateway
resource "google_api_gateway_api_config" "api_config" {
  count         = var.use_api_gateway ? 1 : 0  
  provider      = google-beta
  project       = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  api           = var.use_api_gateway ? google_api_gateway_api.api[0].api_id : ""
  api_config_id = "${var.api_config_name}-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  
  openapi_documents {
    document {
      path = "spec.yaml"
      contents = base64encode(<<-EOT
        swagger: '2.0'
        info:
          title: PALIOS-TAEY API
          description: API Gateway for PALIOS-TAEY services
          version: 1.0.0
        schemes:
          - https
        produces:
          - application/json
        paths:
          /:
            get:
              summary: API Health check
              operationId: health
              x-google-backend:
                address: ${google_cloud_run_service.palios_taey_service.status[0].url}/health
              responses:
                '200':
                  description: Successful operation
          /api/{path+}:
            x-google-backend:
              address: ${google_cloud_run_service.palios_taey_service.status[0].url}/api/{path}
            get:
              summary: Forward GET requests to Cloud Run service
              operationId: apiGet
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            post:
              summary: Forward POST requests to Cloud Run service
              operationId: apiPost
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            put:
              summary: Forward PUT requests to Cloud Run service
              operationId: apiPut
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            delete:
              summary: Forward DELETE requests to Cloud Run service
              operationId: apiDelete
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
          /leader/{path+}:
            x-google-backend:
              address: ${google_cloud_run_service.palios_taey_service.status[0].url}/leader/{path}
            get:
              summary: Forward leader GET requests to Cloud Run service
              operationId: leaderGet
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            post:
              summary: Forward leader POST requests to Cloud Run service
              operationId: leaderPost
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
          /memory/{path+}:
            x-google-backend:
              address: ${google_cloud_run_service.palios_taey_service.status[0].url}/memory/{path}
            get:
              summary: Forward memory GET requests to Cloud Run service
              operationId: memoryGet
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            post:
              summary: Forward memory POST requests to Cloud Run service
              operationId: memoryPost
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
          /transcript/{path+}:
            x-google-backend:
              address: ${google_cloud_run_service.palios_taey_service.status[0].url}/transcript/{path}
            get:
              summary: Forward transcript GET requests to Cloud Run service
              operationId: transcriptGet
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            post:
              summary: Forward transcript POST requests to Cloud Run service
              operationId: transcriptPost
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
          /models/{path+}:
            x-google-backend:
              address: ${google_cloud_run_service.palios_taey_service.status[0].url}/models/{path}
            get:
              summary: Forward models GET requests to Cloud Run service
              operationId: modelsGet
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
            post:
              summary: Forward models POST requests to Cloud Run service
              operationId: modelsPost
              parameters:
                - name: path
                  in: path
                  required: true
                  type: string
              responses:
                '200':
                  description: Successful operation
        securityDefinitions:
          api_key:
            type: apiKey
            name: X-API-Key
            in: header
      EOT
      )
    }
  }
  
  gateway_config {
    backend_config {
      google_service_account = google_service_account.api_gateway_service_account.email
    }
  }
  
  lifecycle {
    create_before_destroy = true
  }
  
  depends_on = [
    google_api_gateway_api.api[0],
    google_cloud_run_service.palios_taey_service,
    google_service_account.api_gateway_service_account
  ]
}

# Create an API Gateway
resource "google_api_gateway_gateway" "api_gateway" {
  count        = var.use_api_gateway ? 1 : 0
  provider     = google-beta
  project      = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  api_config = google_api_gateway_api_config.api_config[0].id
  gateway_id   = var.api_gateway_name
  region       = var.region
  
  display_name = "PALIOS-TAEY API Gateway"
  
  depends_on = [google_api_gateway_api_config.api_config[0]]
}