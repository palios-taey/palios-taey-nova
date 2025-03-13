"""
GitHub integration utility for Claude interaction with the repository.

This script facilitates direct Claude-GitHub interaction with methods for:
1. Reading repository files
2. Creating/updating branches
3. Committing changes
4. Creating pull requests
"""
import os
import base64
import time
import requests
import jwt
from typing import Dict, List, Optional, Union, Any


class GitHubIntegration:
    """GitHub API integration for Claude."""
    
    def __init__(
        self,
        app_id: str,
        installation_id: str,
        private_key_path: str,
        organization: str,
        repository: str,
    ):
        """
        Initialize the GitHub integration.
        
        Args:
            app_id: GitHub App ID
            installation_id: GitHub App installation ID
            private_key_path: Path to the private key file
            organization: GitHub organization name
            repository: GitHub repository name
        """
        self.app_id = app_id
        self.installation_id = installation_id
        self.private_key_path = private_key_path
        self.organization = organization
        self.repository = repository
        self.api_url = "https://api.github.com"
        
        # Load private key
        with open(private_key_path, "r") as key_file:
            self.private_key = key_file.read()
    
    def get_jwt_token(self) -> str:
        """
        Generate a JWT for GitHub App authentication.
        
        Returns:
            JWT token
        """
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + (10 * 60),  # 10 minutes expiration
            "iss": self.app_id,
        }
        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        return token
    
    def get_installation_token(self) -> str:
        """
        Get an installation access token for the GitHub App.
        
        Returns:
            Installation token
        """
        jwt_token = self.get_jwt_token()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.post(
            f"{self.api_url}/app/installations/{self.installation_id}/access_tokens",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()["token"]
    
    def get_file_content(self, path: str, ref: str = "main") -> str:
        """
        Get the content of a file from the repository.
        
        Args:
            path: File path in the repository
            ref: Git reference (branch, tag, or commit)
            
        Returns:
            File content as string
        """
        token = self.get_installation_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(
            f"{self.api_url}/repos/{self.organization}/{self.repository}/contents/{path}",
            headers=headers,
            params={"ref": ref},
        )
        response.raise_for_status()
        content = response.json()["content"]
        return base64.b64decode(content).decode("utf-8")
    
    def get_file_sha(self, path: str, ref: str = "main") -> Optional[str]:
        """
        Get the SHA of a file in the repository.
        
        Args:
            path: File path in the repository
            ref: Git reference (branch, tag, or commit)
            
        Returns:
            File SHA or None if the file doesn't exist
        """
        token = self.get_installation_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(
            f"{self.api_url}/repos/{self.organization}/{self.repository}/contents/{path}",
            headers=headers,
            params={"ref": ref},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()["sha"]
    
    def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Create or update a file in the repository.
        
        Args:
            path: File path in the repository
            content: File content
            message: Commit message
            branch: Branch name
            
        Returns:
            API response
        """
        token = self.get_installation_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Check if file exists and get its SHA
        sha = self.get_file_sha(path, branch)
        
        # Prepare request data
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        
        if sha:
            data["sha"] = sha
        
        # Create or update the file
        response = requests.put(
            f"{self.api_url}/repos/{self.organization}/{self.repository}/contents/{path}",
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, name: str, from_branch: str = "main") -> Dict[str, Any]:
        """
        Create a new branch in the repository.
        
        Args:
            name: Branch name
            from_branch: Source branch
            
        Returns:
            API response
        """
        token = self.get_installation_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Get the SHA of the latest commit on the source branch
        response = requests.get(
            f"{self.api_url}/repos/{self.organization}/{self.repository}/git/refs/heads/{from_branch}",
            headers=headers,
        )
        response.raise_for_status()
        sha = response.json()["object"]["sha"]
        
        # Create the new branch
        data = {
            "ref": f"refs/heads/{name}",
            "sha": sha,
        }
        response = requests.post(
            f"{self.api_url}/repos/{self.organization}/{self.repository}/git/refs",
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            title: Pull request title
            body: Pull request body
            head: Source branch
            base: Target branch
            
        Returns:
            API response
        """
        token = self.get_installation_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        response = requests.post(
            f"{self.api_url}/repos/{self.organization}/{self.repository}/pulls",
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Replace with your actual values
    github = GitHubIntegration(
        app_id="YOUR_APP_ID",
        installation_id="YOUR_INSTALLATION_ID",
        private_key_path="path/to/private-key.pem",
        organization="palios-taey",
        repository="palios-taey-nova",
    )
    
    # Test authentication
    token = github.get_installation_token()
    print(f"Successfully obtained installation token: {token[:10]}...")
