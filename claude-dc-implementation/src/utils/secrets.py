#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Secrets Utility
------------------------------------
This module provides utilities for securely handling secrets.
It supports loading secrets from environment variables or a local file.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("secrets_util")

# Default paths
DEFAULT_ENV_PATH = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/.env")
DEFAULT_SECRETS_PATH = Path("/home/jesse/secrets/palios-taey-secrets.json")
DEFAULT_CREDENTIALS_PATH = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/credentials/service_account.json")

class SecretsManager:
    """Utility class for securely handling secrets."""
    
    def __init__(self, 
                env_path: Optional[Path] = None, 
                secrets_path: Optional[Path] = None,
                credentials_path: Optional[Path] = None):
        """
        Initialize secrets manager.
        
        Args:
            env_path: Path to .env file
            secrets_path: Path to secrets.json file
            credentials_path: Path to service account credentials file
        """
        self.env_path = env_path or DEFAULT_ENV_PATH
        self.secrets_path = secrets_path or DEFAULT_SECRETS_PATH
        self.credentials_path = credentials_path or DEFAULT_CREDENTIALS_PATH
        
        # Cache for secrets
        self._env_vars = None
        self._secrets = None
        self._credentials = None
    
    def _load_env_vars(self) -> Dict[str, str]:
        """
        Load environment variables from .env file.
        
        Returns:
            Dictionary of environment variables
        """
        if self._env_vars is not None:
            return self._env_vars
        
        env_vars = {}
        
        # First check if .env file exists
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key] = value
                    
                    # Also set in environment for libraries that use os.environ
                    if key not in os.environ:
                        os.environ[key] = value
        
        self._env_vars = env_vars
        return env_vars
    
    def _load_secrets(self) -> Dict[str, Any]:
        """
        Load secrets from secrets.json file.
        
        Returns:
            Dictionary of secrets
        """
        if self._secrets is not None:
            return self._secrets
        
        # Check if file exists
        if not self.secrets_path.exists():
            logger.warning(f"Secrets file not found at {self.secrets_path}")
            return {}
        
        try:
            with open(self.secrets_path, 'r') as f:
                secrets = json.load(f)
            
            self._secrets = secrets
            return secrets
        except Exception as e:
            logger.error(f"Error loading secrets: {str(e)}")
            return {}
    
    def _load_credentials(self) -> Dict[str, Any]:
        """
        Load credentials from service account file.
        
        Returns:
            Dictionary of credentials
        """
        if self._credentials is not None:
            return self._credentials
        
        # Check if file exists
        if not self.credentials_path.exists():
            logger.warning(f"Credentials file not found at {self.credentials_path}")
            return {}
        
        try:
            with open(self.credentials_path, 'r') as f:
                credentials = json.load(f)
            
            self._credentials = credentials
            return credentials
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return {}
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Name of the provider (anthropic, openai, etc.)
        
        Returns:
            API key or None if not found
        """
        # First try environment variables
        env_vars = self._load_env_vars()
        
        # Check specific environment variable formats
        if provider.lower() == "anthropic":
            if "ANTHROPIC_API_KEY" in env_vars:
                return env_vars["ANTHROPIC_API_KEY"]
        elif provider.lower() == "openai":
            if "OPENAI_API_KEY" in env_vars:
                return env_vars["OPENAI_API_KEY"]
        elif provider.lower() == "google" or provider.lower() == "google_ai_studio":
            if "GOOGLE_AI_STUDIO_KEY" in env_vars:
                return env_vars["GOOGLE_AI_STUDIO_KEY"]
        elif provider.lower() == "grok" or provider.lower() == "xai_grok":
            if "XAI_GROK_API_KEY" in env_vars:
                return env_vars["XAI_GROK_API_KEY"]
        
        # If not found in environment variables, try secrets file
        secrets = self._load_secrets()
        if "api_keys" in secrets and provider.lower() in secrets["api_keys"]:
            return secrets["api_keys"][provider.lower()]
        
        # Check alternative keys in secrets
        if "api_keys" in secrets:
            api_keys = secrets["api_keys"]
            if provider.lower() == "anthropic" and "anthropic" in api_keys:
                return api_keys["anthropic"]
            elif provider.lower() == "openai" and "openai" in api_keys:
                return api_keys["openai"]
            elif provider.lower() in ["google", "google_ai_studio"] and "google_ai_studio" in api_keys:
                return api_keys["google_ai_studio"]
            elif provider.lower() in ["grok", "xai_grok"] and "xai_grok" in api_keys:
                return api_keys["xai_grok"]
        
        logger.warning(f"API key for {provider} not found")
        return None
    
    def get_gcp_project_id(self) -> Optional[str]:
        """
        Get Google Cloud project ID.
        
        Returns:
            Project ID or None if not found
        """
        # First try environment variables
        env_vars = self._load_env_vars()
        if "GCP_PROJECT_ID" in env_vars:
            return env_vars["GCP_PROJECT_ID"]
        
        # If not found in environment variables, try secrets file
        secrets = self._load_secrets()
        if "gcp" in secrets and "project_id" in secrets["gcp"]:
            return secrets["gcp"]["project_id"]
        
        # As a last resort, try service account credentials
        credentials = self._load_credentials()
        if "project_id" in credentials:
            return credentials["project_id"]
        
        logger.warning("GCP project ID not found")
        return None
    
    def get_gcp_credentials(self) -> Dict[str, Any]:
        """
        Get Google Cloud service account credentials.
        
        Returns:
            Dictionary containing service account credentials
        """
        return self._load_credentials()
    
    def get_webhook_secret(self) -> Optional[str]:
        """
        Get webhook secret.
        
        Returns:
            Webhook secret or None if not found
        """
        # First try environment variables
        env_vars = self._load_env_vars()
        if "WEBHOOK_SECRET" in env_vars:
            return env_vars["WEBHOOK_SECRET"]
        
        # If not found in environment variables, try secrets file
        secrets = self._load_secrets()
        if "webhook" in secrets and "secret" in secrets["webhook"]:
            return secrets["webhook"]["secret"]
        
        logger.warning("Webhook secret not found")
        return None
    
    def get_webhook_url(self) -> Optional[str]:
        """
        Get webhook URL.
        
        Returns:
            Webhook URL or None if not found
        """
        # First try environment variables
        env_vars = self._load_env_vars()
        if "WEBHOOK_URL" in env_vars:
            return env_vars["WEBHOOK_URL"]
        
        # If not found in environment variables, try secrets file
        secrets = self._load_secrets()
        if "webhook" in secrets and "url" in secrets["webhook"]:
            return secrets["webhook"]["url"]
        
        # Default webhook URL
        return "http://localhost:8000/webhook"


# Create a singleton instance for global use
secrets_manager = SecretsManager()

def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a specific provider.
    
    Args:
        provider: Name of the provider (anthropic, openai, etc.)
    
    Returns:
        API key or None if not found
    """
    return secrets_manager.get_api_key(provider)

def get_gcp_project_id() -> Optional[str]:
    """
    Get Google Cloud project ID.
    
    Returns:
        Project ID or None if not found
    """
    return secrets_manager.get_gcp_project_id()

def get_gcp_credentials() -> Dict[str, Any]:
    """
    Get Google Cloud service account credentials.
    
    Returns:
        Dictionary containing service account credentials
    """
    return secrets_manager.get_gcp_credentials()

def get_webhook_secret() -> Optional[str]:
    """
    Get webhook secret.
    
    Returns:
        Webhook secret or None if not found
    """
    return secrets_manager.get_webhook_secret()

def get_webhook_url() -> Optional[str]:
    """
    Get webhook URL.
    
    Returns:
        Webhook URL or None if not found
    """
    return secrets_manager.get_webhook_url()


if __name__ == "__main__":
    # Test the secrets manager
    print("Testing secrets manager...")
    
    anthropic_key = get_api_key("anthropic")
    print(f"Anthropic API key found: {anthropic_key is not None}")
    
    openai_key = get_api_key("openai")
    print(f"OpenAI API key found: {openai_key is not None}")
    
    gcp_project_id = get_gcp_project_id()
    print(f"GCP project ID: {gcp_project_id}")
    
    webhook_url = get_webhook_url()
    print(f"Webhook URL: {webhook_url}")
    
    webhook_secret = get_webhook_secret()
    print(f"Webhook secret found: {webhook_secret is not None}")