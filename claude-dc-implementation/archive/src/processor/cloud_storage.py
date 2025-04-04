#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Cloud Storage
---------------------------------
This module handles integration with Google Cloud Storage for persisting
processed transcripts and patterns.
"""

import os
import json
import logging
import sys
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import utilities
from src.utils.secrets import get_gcp_project_id, get_gcp_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cloud_storage")

# Global variables
gcs_client = None
firestore_client = None

def initialize_gcp_clients():
    """Initialize Google Cloud clients."""
    global gcs_client, firestore_client
    
    try:
        # Import GCP libraries
        from google.cloud import storage
        from google.cloud import firestore
        
        # Get GCP project ID
        project_id = get_gcp_project_id()
        if not project_id:
            logger.warning("No GCP project ID found. Using default project.")
        
        # Initialize Storage client
        gcs_client = storage.Client(project=project_id)
        logger.info(f"Initialized GCS client for project: {project_id}")
        
        # Initialize Firestore client
        firestore_client = firestore.Client(project=project_id)
        logger.info(f"Initialized Firestore client for project: {project_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {e}")
        return False

def upload_to_gcs(bucket_name: str, source_path: str, destination_blob_name: str) -> bool:
    """
    Upload a file to Google Cloud Storage.
    
    Args:
        bucket_name: Name of the GCS bucket
        source_path: Path to the local file to upload
        destination_blob_name: Name to give the uploaded file in GCS
    
    Returns:
        Boolean indicating if the upload was successful
    """
    global gcs_client
    
    # Initialize client if needed
    if gcs_client is None:
        initialize_gcp_clients()
    
    if gcs_client is None:
        logger.error("GCS client not initialized. Cannot upload file.")
        return False
    
    try:
        # Get the bucket
        bucket = gcs_client.bucket(bucket_name)
        
        # Create a blob object from the bucket
        blob = bucket.blob(destination_blob_name)
        
        # Upload the file
        blob.upload_from_filename(source_path)
        
        logger.info(f"File {source_path} uploaded to gs://{bucket_name}/{destination_blob_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        return False

def download_from_gcs(bucket_name: str, source_blob_name: str, destination_path: str) -> bool:
    """
    Download a file from Google Cloud Storage.
    
    Args:
        bucket_name: Name of the GCS bucket
        source_blob_name: Name of the file in GCS to download
        destination_path: Path to save the downloaded file
    
    Returns:
        Boolean indicating if the download was successful
    """
    global gcs_client
    
    # Initialize client if needed
    if gcs_client is None:
        initialize_gcp_clients()
    
    if gcs_client is None:
        logger.error("GCS client not initialized. Cannot download file.")
        return False
    
    try:
        # Get the bucket
        bucket = gcs_client.bucket(bucket_name)
        
        # Create a blob object from the bucket
        blob = bucket.blob(source_blob_name)
        
        # Download the file
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        blob.download_to_filename(destination_path)
        
        logger.info(f"File gs://{bucket_name}/{source_blob_name} downloaded to {destination_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download from GCS: {e}")
        return False

def store_transcript_patterns(patterns: Dict[str, Any], transcript_id: str, bucket_name: str = None) -> str:
    """
    Store transcript patterns in Google Cloud Storage.
    
    Args:
        patterns: Dictionary containing the patterns
        transcript_id: ID of the transcript
        bucket_name: Name of the GCS bucket (optional)
    
    Returns:
        Path to the stored file in GCS or None if failed
    """
    # Default bucket
    if bucket_name is None:
        bucket_name = "palios-taey-patterns"
    
    # Create a temporary file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_file = f"/tmp/patterns_{transcript_id}_{timestamp}.json"
    
    try:
        # Write patterns to temporary file
        with open(temp_file, 'w') as f:
            json.dump(patterns, f, indent=2)
        
        # Upload to GCS
        destination_blob_name = f"patterns/{transcript_id}/{timestamp}.json"
        success = upload_to_gcs(bucket_name, temp_file, destination_blob_name)
        
        # Clean up temporary file
        os.remove(temp_file)
        
        if success:
            # Store reference in Firestore
            if firestore_client is not None:
                try:
                    # Get the patterns collection
                    patterns_collection = firestore_client.collection("patterns")
                    
                    # Add pattern document
                    doc_ref = patterns_collection.document(f"{transcript_id}_{timestamp}")
                    doc_ref.set({
                        "transcript_id": transcript_id,
                        "timestamp": datetime.now(),
                        "storage_path": f"gs://{bucket_name}/{destination_blob_name}",
                        "pattern_count": sum(len(patterns[k]) for k in patterns if isinstance(patterns[k], list)),
                        "pattern_types": list(patterns.keys())
                    })
                    
                    logger.info(f"Pattern reference stored in Firestore: {transcript_id}_{timestamp}")
                    
                except Exception as e:
                    logger.error(f"Failed to store pattern reference in Firestore: {e}")
            
            return f"gs://{bucket_name}/{destination_blob_name}"
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to store transcript patterns: {e}")
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return None

def load_transcript_patterns(path: str) -> Dict[str, Any]:
    """
    Load transcript patterns from Google Cloud Storage.
    
    Args:
        path: GCS path to the patterns file
    
    Returns:
        Dictionary containing the patterns
    """
    # Parse the GCS path
    if not path.startswith("gs://"):
        logger.error(f"Invalid GCS path: {path}")
        return None
    
    path = path[5:]  # Remove gs://
    bucket_name, blob_name = path.split("/", 1)
    
    # Create a temporary file
    temp_file = f"/tmp/patterns_{os.urandom(4).hex()}.json"
    
    try:
        # Download from GCS
        success = download_from_gcs(bucket_name, blob_name, temp_file)
        
        if success:
            # Read patterns from temporary file
            with open(temp_file, 'r') as f:
                patterns = json.load(f)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            return patterns
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to load transcript patterns: {e}")
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return None

def list_stored_patterns() -> List[Dict[str, Any]]:
    """
    List all stored patterns in Firestore.
    
    Returns:
        List of dictionaries containing pattern metadata
    """
    global firestore_client
    
    # Initialize client if needed
    if firestore_client is None:
        initialize_gcp_clients()
    
    if firestore_client is None:
        logger.error("Firestore client not initialized. Cannot list patterns.")
        return []
    
    try:
        # Get the patterns collection
        patterns_collection = firestore_client.collection("patterns")
        
        # Get all documents
        docs = patterns_collection.stream()
        
        # Convert to list of dictionaries
        patterns = []
        for doc in docs:
            pattern_data = doc.to_dict()
            pattern_data["id"] = doc.id
            patterns.append(pattern_data)
        
        return patterns
        
    except Exception as e:
        logger.error(f"Failed to list stored patterns: {e}")
        return []


if __name__ == "__main__":
    # Test the cloud storage functionality
    initialize_gcp_clients()
    
    # Check if GCS is initialized
    if gcs_client is None:
        print("GCS client not initialized. Some features will be unavailable.")
    else:
        print("GCS client initialized successfully.")
    
    # Check if Firestore is initialized
    if firestore_client is None:
        print("Firestore client not initialized. Some features will be unavailable.")
    else:
        print("Firestore client initialized successfully.")
        
        # List patterns
        patterns = list_stored_patterns()
        print(f"Found {len(patterns)} stored patterns.")
        
        # Print first pattern if available
        if patterns:
            print(f"First pattern: {patterns[0]}")