# GitHub Connection Guide for Claude

This document outlines the approach for establishing a direct connection between Claude and the PALIOS-TAEY GitHub repository.

## Overview

To enable Claude to interact directly with the GitHub repository, we'll use a GitHub App with appropriate permissions. This allows Claude to:
- Read repository files
- Create and update branches
- Commit changes
- Create pull requests

## GitHub App Approach

### 1. Create a GitHub App

1. Go to the GitHub organization settings
2. Navigate to Developer settings → GitHub Apps → New GitHub App
3. Configure the app:
   - Name: `claude-palios-taey`
   - Homepage URL: (Your project website or GitHub organization URL)
   - Webhook: Disable for now
   - Permissions:
     - Repository permissions:
       - Contents: Read & write (for reading/writing repository files)
       - Pull requests: Read & write (for creating/managing PRs)
       - Metadata: Read-only (required)
   - Where can this GitHub App be installed?: Only on this account

4. Generate and download a private key
5. Install the app on your organization

### 2. Integration Implementation

The integration between Claude and GitHub is implemented in `scripts/github_integration.py`. This script provides:

```python
class GitHubIntegration:
    """GitHub API integration for Claude."""
    
    def __init__(self, app_id, installation_id, private_key_path, organization, repository):
        """Initialize the GitHub integration."""
        # ...
    
    def get_file_content(self, path, ref="main"):
        """Get the content of a file from the repository."""
        # ...
    
    def create_or_update_file(self, path, content, message, branch="main"):
        """Create or update a file in the repository."""
        # ...
    
    def create_branch(self, name, from_branch="main"):
        """Create a new branch in the repository."""
        # ...
    
    def create_pull_request(self, title, body, head, base="main"):
        """Create a pull request."""
        # ...
3. Configuration
Store the GitHub App credentials securely:
CopyAPP_ID=your-app-id
INSTALLATION_ID=your-installation-id
PRIVATE_KEY_PATH=path/to/private-key.pem
ORGANIZATION=palios-taey
REPOSITORY=palios-taey-nova
4. Usage Example
pythonCopyfrom scripts.github_integration import GitHubIntegration

# Initialize GitHub integration
github = GitHubIntegration(
    app_id="your-app-id",
    installation_id="your-installation-id",
    private_key_path="path/to/private-key.pem",
    organization="palios-taey",
    repository="palios-taey-nova",
)

# Read a file
content = github.get_file_content("src/main.py")

# Update a file
github.create_or_update_file(
    path="src/main.py",
    content="Updated content",
    message="Update main.py",
    branch="feature/update-main",
)

# Create a pull request
github.create_pull_request(
    title="Update main.py",
    body="This PR updates main.py with new functionality.",
    head="feature/update-main",
    base="main",
)
Alternative: Personal Access Token
If the GitHub App approach proves too complex, a simpler alternative is to use a Personal Access Token (PAT):

Create a fine-grained personal access token with the needed permissions
Store the token securely
Use the token for GitHub API requests

pythonCopyimport requests

def get_file_content(repo, path, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()["content"]
Security Considerations

Store credentials securely (never commit them to the repository)
Use the principle of least privilege when setting permissions
Regularly rotate credentials
Monitor GitHub App activity

Next Steps

Create the GitHub App in the organization settings
Generate and securely store the private key
Install the app on the repository
Test the integration with basic operations
Expand the integration as needed for the project
