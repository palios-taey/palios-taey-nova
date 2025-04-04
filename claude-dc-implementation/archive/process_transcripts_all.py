#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Process All Transcripts
-------------------------------------------
This script processes all transcripts from the provided examples folder,
extracts patterns using mathematical sampling, and stores the results.
"""

import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import modules from conductor framework
from src.processor.transcript_processor import TranscriptProcessor
from src.processor.transcript_loader import TranscriptLoader
from src.processor.cloud_storage import (
    initialize_gcp_clients, 
    store_transcript_patterns,
    list_stored_patterns
)
from src.utils.secrets import get_gcp_project_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/process_transcripts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("process_transcripts")

def process_transcripts(transcripts_dir: str, 
                      output_dir: str,
                      cloud_storage: bool = False, 
                      batch_size: int = 10,
                      max_files: Optional[int] = None):
    """
    Process transcripts and extract patterns.
    
    Args:
        transcripts_dir: Directory containing transcripts
        output_dir: Directory to store output
        cloud_storage: Whether to store results in cloud storage
        batch_size: Number of transcripts to process in each batch
        max_files: Maximum number of files to process (or None for all)
    """
    # Initialize cloud storage if needed
    if cloud_storage:
        initialize_gcp_clients()
    
    # Initialize transcript loader and processor
    loader = TranscriptLoader(base_dir=transcripts_dir)
    processor = TranscriptProcessor()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process transcripts in batches
    total_processed = 0
    total_patterns = 0
    
    # Keep track of source counts
    source_counts = {}
    
    # Process each source separately to ensure balance
    for source in ["claude", "chatgpt", "grok", "gemini"]:
        # Load transcripts for this source
        transcripts = loader.load_transcripts(source=source, max_files=max_files)
        
        # Skip if no transcripts found
        if not transcripts:
            logger.info(f"No transcripts found for source: {source}")
            continue
        
        # Update source counts
        source_counts[source] = len(transcripts)
        total_processed += len(transcripts)
        
        # Process the transcripts
        logger.info(f"Processing {len(transcripts)} transcripts from {source}")
        
        # Process in batches
        for i in range(0, len(transcripts), batch_size):
            batch = transcripts[i:i+batch_size]
            
            # Process the batch
            results = processor.process_transcript_batch(batch)
            
            # Update pattern count
            batch_pattern_count = results.get("metrics", {}).get("total_patterns", 0)
            total_patterns += batch_pattern_count
            
            # Store the results
            timestamp = int(time.time())
            output_file = os.path.join(output_dir, f"patterns_{source}_{i}_{timestamp}.json")
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Stored {batch_pattern_count} patterns from batch {i//batch_size + 1} in {output_file}")
            
            # Store in cloud storage if enabled
            if cloud_storage and "patterns" in results:
                for j, transcript in enumerate(batch):
                    # Generate a transcript ID
                    transcript_id = f"{source}_{i + j}_{timestamp}"
                    
                    # Get patterns for this transcript
                    transcript_patterns = {}
                    for pattern_type, patterns in results["patterns"].items():
                        transcript_patterns[pattern_type] = [p for p in patterns if p.get("source") == transcript.get("source")]
                    
                    # Store in cloud storage
                    storage_path = store_transcript_patterns(transcript_patterns, transcript_id)
                    
                    if storage_path:
                        logger.info(f"Stored patterns for transcript {transcript_id} in {storage_path}")
    
    # Generate overall pattern report
    pattern_report = processor.generate_pattern_report()
    
    # Add processing metadata
    pattern_report["processing_metadata"] = {
        "timestamp": time.time(),
        "total_transcripts_processed": total_processed,
        "total_patterns_extracted": total_patterns,
        "source_counts": source_counts,
        "using_cloud_storage": cloud_storage
    }
    
    # Save pattern report
    report_file = os.path.join(output_dir, "pattern_report.json")
    with open(report_file, 'w') as f:
        json.dump(pattern_report, f, indent=2)
    
    logger.info(f"Pattern report saved to {report_file}")
    
    # Export visualization data
    viz_data_file = os.path.join(output_dir, "visualization_data.json")
    processor.export_for_visualization(viz_data_file)
    
    logger.info(f"Visualization data exported to {viz_data_file}")
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total transcripts processed: {total_processed}")
    print(f"Total patterns extracted: {total_patterns}")
    print(f"Source counts: {source_counts}")
    print(f"Pattern report saved to: {report_file}")
    print(f"Visualization data exported to: {viz_data_file}")


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Process transcripts and extract patterns")
    parser.add_argument(
        "--transcripts-dir",
        default="/transcripts/examples",
        help="Directory containing transcripts (default: /transcripts/examples)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/patterns",
        help="Directory to store output (default: data/patterns)"
    )
    parser.add_argument(
        "--cloud-storage",
        action="store_true",
        help="Store results in cloud storage"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of transcripts to process in each batch (default: 10)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of files to process per source (default: all)"
    )
    
    args = parser.parse_args()
    
    # Process transcripts
    process_transcripts(
        transcripts_dir=args.transcripts_dir,
        output_dir=args.output_dir,
        cloud_storage=args.cloud_storage,
        batch_size=args.batch_size,
        max_files=args.max_files
    )