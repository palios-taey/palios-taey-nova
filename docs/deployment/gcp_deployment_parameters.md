# GCP Deployment Parameters
Generated on: Tue Mar 18 17:15:48 EDT 2025

## Current Authentication
- **Admin Account**: `jesse@taey.ai`

## Organization & Project Identifiers
- **Organizations**:
  - taey.ai	135174585026

- **Current Project**:
  - Name: `palios-taey-dev`
  - Number: `44790150696`

- **Default Region**: ``
- **Default Zone**: ``

## Service Accounts
```
EMAIL                                                                   DISPLAY_NAME
palios-taey-runner@palios-taey-dev.iam.gserviceaccount.com
palios-taey-firestore-sa-palio@palios-taey-dev.iam.gserviceaccount.com
palios-taey-test-sa@palios-taey-dev.iam.gserviceaccount.com
palios-taey-admin-sa-palios-ta@palios-taey-dev.iam.gserviceaccount.com
44790150696-compute@developer.gserviceaccount.com
palios-taey-cloudrun-sa-palios@palios-taey-dev.iam.gserviceaccount.com
```

## Artifact Registry
```
REPOSITORY               FORMAT  LOCATION     ENCRYPTION
cloud-run-source-deploy  DOCKER  us-central1  Google-managed key
palios-taey              DOCKER  us-central1  Google-managed key
palios-taey-repo         DOCKER  us-central1  Google-managed key
```

### Registry Paths
- `-docker.pkg.dev/palios-taey-dev/cloud-run-source-deploy`
- `-docker.pkg.dev/palios-taey-dev/palios-taey`
- `-docker.pkg.dev/palios-taey-dev/palios-taey-repo`

## Networking
### VPC Networks
```
NAME                 SUBNET_MODE  IPV4_RANGE
default              AUTO
palios-taey-network  AUTO
```

### Subnets
```
NAME                 REGION                   NETWORK              RANGE
default              us-central1              default              10.128.0.0/20
palios-taey-network  us-central1              palios-taey-network  10.128.0.0/20
default              europe-west1             default              10.132.0.0/20
palios-taey-network  europe-west1             palios-taey-network  10.132.0.0/20
default              us-west1                 default              10.138.0.0/20
palios-taey-network  us-west1                 palios-taey-network  10.138.0.0/20
default              asia-east1               default              10.140.0.0/20
palios-taey-network  asia-east1               palios-taey-network  10.140.0.0/20
default              us-east1                 default              10.142.0.0/20
palios-taey-network  us-east1                 palios-taey-network  10.142.0.0/20
default              asia-northeast1          default              10.146.0.0/20
palios-taey-network  asia-northeast1          palios-taey-network  10.146.0.0/20
default              asia-southeast1          default              10.148.0.0/20
palios-taey-network  asia-southeast1          palios-taey-network  10.148.0.0/20
default              us-east4                 default              10.150.0.0/20
palios-taey-network  us-east4                 palios-taey-network  10.150.0.0/20
default              australia-southeast1     default              10.152.0.0/20
palios-taey-network  australia-southeast1     palios-taey-network  10.152.0.0/20
default              europe-west2             default              10.154.0.0/20
palios-taey-network  europe-west2             palios-taey-network  10.154.0.0/20
default              europe-west3             default              10.156.0.0/20
palios-taey-network  europe-west3             palios-taey-network  10.156.0.0/20
default              southamerica-east1       default              10.158.0.0/20
palios-taey-network  southamerica-east1       palios-taey-network  10.158.0.0/20
default              asia-south1              default              10.160.0.0/20
palios-taey-network  asia-south1              palios-taey-network  10.160.0.0/20
default              northamerica-northeast1  default              10.162.0.0/20
palios-taey-network  northamerica-northeast1  palios-taey-network  10.162.0.0/20
default              europe-west4             default              10.164.0.0/20
palios-taey-network  europe-west4             palios-taey-network  10.164.0.0/20
default              europe-north1            default              10.166.0.0/20
palios-taey-network  europe-north1            palios-taey-network  10.166.0.0/20
default              us-west2                 default              10.168.0.0/20
palios-taey-network  us-west2                 palios-taey-network  10.168.0.0/20
default              asia-east2               default              10.170.0.0/20
palios-taey-network  asia-east2               palios-taey-network  10.170.0.0/20
default              europe-west6             default              10.172.0.0/20
palios-taey-network  europe-west6             palios-taey-network  10.172.0.0/20
default              asia-northeast2          default              10.174.0.0/20
palios-taey-network  asia-northeast2          palios-taey-network  10.174.0.0/20
default              asia-northeast3          default              10.178.0.0/20
palios-taey-network  asia-northeast3          palios-taey-network  10.178.0.0/20
default              us-west3                 default              10.180.0.0/20
palios-taey-network  us-west3                 palios-taey-network  10.180.0.0/20
default              us-west4                 default              10.182.0.0/20
palios-taey-network  us-west4                 palios-taey-network  10.182.0.0/20
default              asia-southeast2          default              10.184.0.0/20
palios-taey-network  asia-southeast2          palios-taey-network  10.184.0.0/20
default              europe-central2          default              10.186.0.0/20
palios-taey-network  europe-central2          palios-taey-network  10.186.0.0/20
default              northamerica-northeast2  default              10.188.0.0/20
palios-taey-network  northamerica-northeast2  palios-taey-network  10.188.0.0/20
default              asia-south2              default              10.190.0.0/20
palios-taey-network  asia-south2              palios-taey-network  10.190.0.0/20
default              australia-southeast2     default              10.192.0.0/20
palios-taey-network  australia-southeast2     palios-taey-network  10.192.0.0/20
default              southamerica-west1       default              10.194.0.0/20
palios-taey-network  southamerica-west1       palios-taey-network  10.194.0.0/20
default              europe-west8             default              10.198.0.0/20
palios-taey-network  europe-west8             palios-taey-network  10.198.0.0/20
default              europe-west9             default              10.200.0.0/20
palios-taey-network  europe-west9             palios-taey-network  10.200.0.0/20
default              us-east5                 default              10.202.0.0/20
palios-taey-network  us-east5                 palios-taey-network  10.202.0.0/20
default              europe-southwest1        default              10.204.0.0/20
palios-taey-network  europe-southwest1        palios-taey-network  10.204.0.0/20
default              us-south1                default              10.206.0.0/20
palios-taey-network  us-south1                palios-taey-network  10.206.0.0/20
default              me-west1                 default              10.208.0.0/20
palios-taey-network  me-west1                 palios-taey-network  10.208.0.0/20
default              europe-west12            default              10.210.0.0/20
palios-taey-network  europe-west12            palios-taey-network  10.210.0.0/20
default              me-central1              default              10.212.0.0/20
palios-taey-network  me-central1              palios-taey-network  10.212.0.0/20
default              europe-west10            default              10.214.0.0/20
palios-taey-network  europe-west10            palios-taey-network  10.214.0.0/20
default              africa-south1            default              10.218.0.0/20
palios-taey-network  africa-south1            palios-taey-network  10.218.0.0/20
default              northamerica-south1      default              10.224.0.0/20
palios-taey-network  northamerica-south1      palios-taey-network  10.224.0.0/20
default              europe-north2            default              10.226.0.0/20
palios-taey-network  europe-north2            palios-taey-network  10.226.0.0/20
```

### Firewall Rules (Top 10)
```
NAME                    NETWORK  DIRECTION  PRIORITY  ALLOW
default-allow-icmp      default  INGRESS    65534     icmp
default-allow-internal  default  INGRESS    65534     tcp:0-65535,udp:0-65535,icmp
default-allow-rdp       default  INGRESS    65534     tcp:3389
default-allow-ssh       default  INGRESS    65534     tcp:22
```

### Load Balancers
No forwarding rules found.

## Cloud Run Services
```
SERVICE              REGION       URL                                                          LAST_DEPLOYED_TIME
palios-taey          us-central1  https://palios-taey-44790150696.us-central1.run.app
palios-taey-service  us-central1  https://palios-taey-service-44790150696.us-central1.run.app
```

## GKE Clusters
No GKE clusters found.

## Database Instances
### Cloud SQL
No Cloud SQL instances found.

## Storage Buckets
```
gs://palios-taey-dev-terraform-state/
gs://palios-taey-dev_cloudbuild/
gs://run-sources-palios-taey-dev-us-central1/
```

## Secret Manager Secrets
No secrets found or accessible.

