# Claude DC Setup Instructions: Transcript Processing Infrastructure

## Overview
This document provides step-by-step instructions for Claude DC to set up the necessary infrastructure for our transcript processing pipeline. This includes configuring APIs, setting up Firestore database tables, and ensuring the memory service is operational.

## Prerequisites
- Access to the PALIOS-TAEY GitHub repository
- Google Cloud Platform account with Firestore enabled
- API keys for required services
- Docker environment for running the processing pipeline

## Step 1: Set Up Google Cloud Firestore

### 1.1 Configure Firestore Database
```bash
# Install Google Cloud SDK if not already installed
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-386.0.0-linux-x86_64.tar.gz
tar -xf google-cloud-sdk-386.0.0-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh

# Initialize gcloud
gcloud init

# Make sure Firestore API is enabled
gcloud services enable firestore.googleapis.com

# Set project ID
gcloud config set project palios-taey-dev
```

### 1.2 Create Firestore Collections
The memory service requires these collections in Firestore:
- `memory_items`: Stores processed transcript insights
- `memory_contexts`: Manages context groupings for related insights
- `memory_relationships`: Tracks relationships between memory items
- `memory_agents`: Stores information about AI agents

Use the following Python script to create these collections if they don't exist:

```python
# save as setup_firestore.py
from google.cloud import firestore

def setup_firestore_collections():
    """Create required Firestore collections if they don't exist."""
    db = firestore.Client()
    
    # Create collections with a placeholder document (required for empty collections)
    collections = [
        'memory_items',
        'memory_contexts',
        'memory_relationships',
        'memory_agents'
    ]
    
    for collection in collections:
        # Check if collection exists by trying to get a document
        docs = list(db.collection(collection).limit(1).stream())
        
        if not docs:
            # Collection doesn't exist or is empty, create placeholder
            placeholder = {
                'id': f'placeholder_{collection}',
                'type': 'placeholder',
                'created_at': firestore.SERVER_TIMESTAMP
            }
            db.collection(collection).document('placeholder').set(placeholder)
            print(f"Created placeholder for collection: {collection}")
        else:
            print(f"Collection already exists: {collection}")
    
    print("Firestore collections setup complete")

if __name__ == "__main__":
    setup_firestore_collections()
```

## Step 2: Configure Memory Service API

### 2.1 Update API Configuration
Edit the configuration file in the repository:

```bash
cd ~/projects/palios-taey-nova
nano src/palios_taey/memory/config.py
```

Update with the correct project ID and authentication settings:

```python
# Memory Service Configuration
MEMORY_CONFIG = {
    "project_id": "palios-taey-dev",  # Update with actual project ID
    "collection_prefix": "",  # Change if needed for dev/prod separation
    "use_emulator": False,    # Set to True for local development
    "cache_size": 1000,       # Adjust based on available system memory
    "tier_transition_config": {
        "t0_to_t1_threshold": 0.3,  # Threshold to move from ephemeral to working
        "t1_to_t2_threshold": 0.6,  # Threshold to move from working to reference
        "t2_to_t3_threshold": 0.2   # Threshold to move from reference to archival
    }
}

# API Authentication Settings
AUTH_CONFIG = {
    "require_auth": False,    # Set to True when ready for production
    "api_key_header": "X-API-Key",
    "valid_api_keys": ["dev_test_key_only"]  # Update with secure keys for production
}
```

### 2.2 Ensure Google Cloud Authentication
Set up authentication for the application:

```bash
# Download service account key file (if using service account)
# NOTE: Keep this file secure and DO NOT commit to GitHub
gcloud iam service-accounts create palios-taey-service
gcloud projects add-iam-policy-binding palios-taey-dev \
    --member="serviceAccount:palios-taey-service@palios-taey-dev.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
gcloud iam service-accounts keys create ~/palios-taey-service-key.json \
    --iam-account=palios-taey-service@palios-taey-dev.iam.gserviceaccount.com

# Set environment variable for authentication
export GOOGLE_APPLICATION_CREDENTIALS=~/palios-taey-service-key.json
```

## Step 3: Set Up Transcript Processing Pipeline

### 3.1 Verify Dependencies
Ensure all required Python packages are installed:

```bash
cd ~/projects/palios-taey-nova
pip install -r requirements.txt

# Add additional requirements if needed
pip install google-cloud-firestore google-cloud-storage pandas nltk scikit-learn
```

### 3.2 Configure Transcript Processor
Update the transcript processor configuration:

```bash
nano src/palios_taey/transcripts/config.py
```

Add the following configuration:

```python
# Transcript processor configuration
TRANSCRIPT_CONFIG = {
    "input_directory": "transcripts",  # Path to transcript files
    "output_directory": "processed",   # Where to store intermediate files
    "formats_supported": ["raw", "deepsearch", "pure_ai", "structured"],
    "chunk_size": 100000,  # Characters per processing chunk
    "overlap_size": 5000,  # Overlap between chunks to maintain context
    "confidence_threshold": 0.7,  # Minimum confidence for tagging
    "max_batch_size": 5,   # Maximum number of files to process in parallel
    "memory_service_context": "transcript_context"  # Context name in memory service
}
```

### 3.3 Create Processing Entry Point
Create a script to initiate transcript processing:

```bash
nano scripts/process_transcripts.py
```

Add the following code:

```python
#!/usr/bin/env python3
"""
Transcript Processing Script for PALIOS-TAEY

This script processes transcript files in the specified directory and
stores the results in the memory service.
"""
import os
import argparse
import logging
import time
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import PALIOS-TAEY components
from palios_taey.memory.service import get_memory_service
from palios_taey.transcripts.processor import create_transcript_processor
from palios_taey.transcripts.format_handler import parse_transcript_format

def process_transcript_file(
    file_path: str,
    format_type: str = "raw",
    memory_service = None,
    transcript_processor = None
) -> str:
    """
    Process a single transcript file.
    
    Args:
        file_path: Path to the transcript file
        format_type: Format of the transcript
        memory_service: Memory service instance
        transcript_processor: Transcript processor instance
        
    Returns:
        transcript_id: ID of the processed transcript
    """
    logger.info(f"Processing transcript file: {file_path}")
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        transcript_data = f.read()
    
    # Extract metadata from filename
    filename = os.path.basename(file_path)
    parts = filename.split("_")
    
    metadata = {
        "source_file": file_path,
        "ai_type": parts[0] if len(parts) > 0 else "unknown",
        "conversation_number": parts[1] if len(parts) > 1 else "unknown",
        "date": parts[2].split(".")[0] if len(parts) > 2 else "unknown"
    }
    
    # Process the transcript
    transcript_id = transcript_processor.process_transcript(
        transcript_data=transcript_data,
        format_type=format_type,
        transcript_id=None,  # Auto-generate ID
        metadata=metadata
    )
    
    logger.info(f"Transcript processed: {transcript_id}")
    return transcript_id

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Process transcript files")
    parser.add_argument("--directory", default="transcripts", help="Directory containing transcript files")
    parser.add_argument("--format", default="raw", choices=["raw", "deepsearch", "pure_ai", "structured"], 
                        help="Transcript format")
    parser.add_argument("--ai-type", help="Only process files for specific AI (e.g., claude, chatgpt)")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    
    args = parser.parse_args()
    
    # Initialize services
    memory_service = get_memory_service()
    transcript_processor = create_transcript_processor(memory_service=memory_service)
    
    # Create transcript context if it doesn't exist
    context_id = "transcript_context"
    context = memory_service.get_context(context_id)
    if not context:
        context_id = memory_service.create_context(
            name="Transcript Analysis",
            description="Context for storing and analyzing transcript data"
        )
        logger.info(f"Created transcript context: {context_id}")
    
    # Get list of transcript files
    base_dir = args.directory
    ai_type = args.ai_type
    transcript_files = []
    
    if ai_type:
        # Process specific AI type
        ai_dir = os.path.join(base_dir, ai_type)
        if os.path.isdir(ai_dir):
            for file in os.listdir(ai_dir):
                if file.endswith(".txt"):
                    transcript_files.append(os.path.join(ai_dir, file))
    else:
        # Process all AIs
        for ai_dir in os.listdir(base_dir):
            ai_path = os.path.join(base_dir, ai_dir)
            if os.path.isdir(ai_path):
                for file in os.listdir(ai_path):
                    if file.endswith(".txt"):
                        transcript_files.append(os.path.join(ai_path, file))
    
    # Sort by filename
    transcript_files.sort()
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        transcript_files = transcript_files[:args.limit]
    
    logger.info(f"Found {len(transcript_files)} transcript files to process")
    
    # Process each file
    processed_ids = []
    
    for file_path in transcript_files:
        try:
            transcript_id = process_transcript_file(
                file_path=file_path,
                format_type=args.format,
                memory_service=memory_service,
                transcript_processor=transcript_processor
            )
            processed_ids.append(transcript_id)
            
            # Sleep briefly to avoid overwhelming the system
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    logger.info(f"Processing complete. Processed {len(processed_ids)} transcripts")
    
    # Create a summary of processed transcripts
    summary = {
        "processed_at": time.time(),
        "transcript_count": len(processed_ids),
        "transcript_ids": processed_ids
    }
    
    memory_service.store(
        content=summary,
        context_id=context_id,
        metadata={
            "type": "processing_summary",
            "count": len(processed_ids)
        },
        tags=["summary", "transcript_processing"]
    )
    
    logger.info("Summary stored in memory service")

if __name__ == "__main__":
    main()
```

Make the script executable:

```bash
chmod +x scripts/process_transcripts.py
```

## Step 4: Test the Setup

### 4.1 Set Up Test Transcript
Create a small test transcript:

```bash
mkdir -p transcripts/claude
echo "This is a test transcript for Claude." > transcripts/claude/claude_test_20240324.txt
```

### 4.2 Run Test Processing
Execute the script with a single test file:

```bash
cd ~/projects/palios-taey-nova
python scripts/process_transcripts.py --ai-type claude --limit 1
```

### 4.3 Verify Results
Check that the test transcript was processed correctly:

```python
# Save as verify_processing.py
from palios_taey.memory.service import get_memory_service

def verify_processing():
    memory_service = get_memory_service()
    
    # Query for processed transcripts
    results = memory_service.query(
        filters={"metadata.ai_type": "claude"},
        limit=10
    )
    
    print(f"Found {len(results)} processed transcripts:")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"ID: {result.get('memory_id')}")
        print(f"Source: {result.get('metadata', {}).get('source_file')}")
        print(f"Tags: {result.get('tags', [])}")
        print(f"Content preview: {str(result.get('content'))[:100]}...")

if __name__ == "__main__":
    verify_processing()
```

Run the verification:

```bash
python verify_processing.py
```

## Step 5: Prepare for Full Processing

### 5.1 Set Up Batch Processing Script
For processing large numbers of transcripts in batches:

```bash
nano scripts/batch_process_transcripts.py
```

Add the following code:

```python
#!/usr/bin/env python3
"""
Batch Transcript Processing Script for PALIOS-TAEY

This script processes transcript files in batches to avoid memory issues.
"""
import os
import argparse
import logging
import time
import subprocess
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def get_transcript_files(base_dir: str, ai_type: str = None) -> List[str]:
    """Get list of transcript files to process."""
    transcript_files = []
    
    if ai_type:
        # Process specific AI type
        ai_dir = os.path.join(base_dir, ai_type)
        if os.path.isdir(ai_dir):
            for file in os.listdir(ai_dir):
                if file.endswith(".txt"):
                    transcript_files.append(os.path.join(ai_dir, file))
    else:
        # Process all AIs
        for ai_dir in os.listdir(base_dir):
            ai_path = os.path.join(base_dir, ai_dir)
            if os.path.isdir(ai_path):
                for file in os.listdir(ai_path):
                    if file.endswith(".txt"):
                        transcript_files.append(os.path.join(ai_path, file))
    
    # Sort by filename
    transcript_files.sort()
    return transcript_files

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Process transcript files in batches")
    parser.add_argument("--directory", default="transcripts", help="Directory containing transcript files")
    parser.add_argument("--format", default="raw", choices=["raw", "deepsearch", "pure_ai", "structured"], 
                        help="Transcript format")
    parser.add_argument("--ai-type", help="Only process files for specific AI (e.g., claude, chatgpt)")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of files to process in each batch")
    parser.add_argument("--sleep", type=int, default=30, help="Seconds to sleep between batches")
    
    args = parser.parse_args()
    
    # Get list of transcript files
    transcript_files = get_transcript_files(args.directory, args.ai_type)
    
    logger.info(f"Found {len(transcript_files)} transcript files to process")
    
    # Process in batches
    batch_count = 0
    
    for i in range(0, len(transcript_files), args.batch_size):
        batch_count += 1
        batch_files = transcript_files[i:i+args.batch_size]
        
        logger.info(f"Processing batch {batch_count} with {len(batch_files)} files")
        
        # Process each batch with the main script
        for file_path in batch_files:
            cmd = [
                "python", "scripts/process_transcripts.py",
                "--format", args.format,
                "--limit", "1"
            ]
            
            # Extract AI type from file path
            path_parts = file_path.split(os.sep)
            file_ai_type = path_parts[-2] if len(path_parts) > 1 else None
            
            if file_ai_type:
                cmd.extend(["--ai-type", file_ai_type])
            
            # Run the process
            logger.info(f"Processing file: {file_path}")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
        
        # Sleep between batches to avoid resource exhaustion
        if i + args.batch_size < len(transcript_files):
            logger.info(f"Sleeping for {args.sleep} seconds before next batch...")
            time.sleep(args.sleep)
    
    logger.info(f"Batch processing complete. Processed {len(transcript_files)} files in {batch_count} batches")

if __name__ == "__main__":
    main()
```

Make the script executable:

```bash
chmod +x scripts/batch_process_transcripts.py
```

## Step 6: Documentation

### 6.1 Create Usage Documentation
Create documentation for how to use the transcript processing pipeline:

```bash
nano docs/transcript_processing.md
```

Add clear instructions for future reference.

### 6.2 Update README.md
Add information about the transcript processing capabilities to the main README.

## Additional Configuration (If Needed)

### Anthropic API Integration
If using the Anthropic API for additional processing:

```bash
# Set API key
export ANTHROPIC_API_KEY=your_api_key_here

# Update configuration
nano src/palios_taey/config/api_config.py
```

Add the following:

```python
# API Configuration
API_CONFIG = {
    "anthropic": {
        "api_key": os.environ.get("ANTHROPIC_API_KEY"),
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000
    }
}
```

## Ready for Processing

Once these steps are completed, the infrastructure will be ready for:
1. Processing the full set of Claude transcripts
2. Storing the processed insights in the memory system
3. Running analysis on the stored data

Please verify each step thoroughly and document any issues encountered during setup.
