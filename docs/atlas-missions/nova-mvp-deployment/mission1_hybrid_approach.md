# ATLAS Mission Brief: GCP Foundation Infrastructure (Hybrid Approach)

## Mission Context
After encountering challenges with fully automated deployment, we're adopting a hybrid approach to establish the GCP foundation for PALIOS-TAEY. This mission focuses on creating essential infrastructure through a combination of manual setup and targeted Terraform configuration.

## Prerequisites (Manually Configured)
The following have been manually configured and should be verified:
- Google Cloud organization created (ID: 135174585026)
- Project "PALIOS-TAEY-dev" established with billing enabled
- Basic authentication and IAM setup completed
- Storage bucket for Terraform state created
- Required GCP APIs enabled:
  * Cloud Run API
  * Firestore API
  * Artifact Registry API
  * IAM API
  * Secret Manager API

## Specific Tasks
1. Create simplified Terraform configurations for core components
2. Establish Firestore database for the Memory System
3. Configure Cloud Run service for application hosting
4. Set up API Gateway for secure external access
5. Create necessary service accounts with appropriate permissions
6. Document all infrastructure including manually configured components

## Scope Boundaries
- IN-SCOPE: Essential GCP infrastructure components required by PALIOS-TAEY
- IN-SCOPE: Simplified Terraform configuration for core components
- IN-SCOPE: Documentation of manual and automated setup steps
- IN-SCOPE: IAM permissions and security settings
- OUT-OF-SCOPE: Complex automation of all infrastructure components
- OUT-OF-SCOPE: CI/CD pipeline configuration (Mission 2)
- OUT-OF-SCOPE: Application-specific environment variables (Mission 3)

## Authority Limits
You have authority to:
- Configure infrastructure components through console or Terraform
- Set up service accounts and permissions
- Document manual configuration steps
- Simplify Terraform configurations as needed

Escalate to CTO Claude if:
- Significant architectural changes are required
- Security vulnerabilities are identified
- Integration issues with other mission components arise

## Required Files and Directories
1. `terraform/` - Directory for all Terraform configurations
   - `main.tf` - Simplified main configuration
   - `variables.tf` - Variables with sensible defaults
   - `outputs.tf` - Essential outputs for subsequent missions
   - `firestore.tf` - Firestore configuration
   - `cloud_run.tf` - Cloud Run configuration
   - `iam.tf` - IAM roles and permissions
   - `network.tf` - Network configuration
2. `scripts/` - Directory for helper scripts
   - `apply_infrastructure.sh` - Script to apply Terraform
3. `docs/` - Documentation directory
   - `manual_setup.md` - Documentation of manual setup steps
   - `infrastructure.md` - Complete infrastructure documentation

## Success Criteria
- Core infrastructure components are successfully configured and operational
- Configuration can be reapplied without errors
- All components are properly documented
- Infrastructure supports the requirements of Missions 2 and 3
- Manual and automated setup steps are clearly distinguished

## Implementation Notes
- Use `cat` commands for all file creation to prevent formatting issues
- Test each component individually before attempting to apply all configurations
- Document any deviations from the original infrastructure design
- Ensure each service account has the minimum required permissions
- Focus on establishing a minimal viable infrastructure first, then enhance as needed