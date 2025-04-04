#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Transcript Processor for Palios-Taey-Nova
--------------------------------------------------
This script processes transcripts from all sources using the enhanced
transcript loader that properly handles complex JSON formats.

Mathematical patterns are extracted using golden ratio and Bach-inspired
sampling methods for more efficient and meaningful pattern recognition.
"""

import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/process_transcripts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("process_all_transcripts")

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the enhanced transcript loader
from src.processor.enhanced_transcript_loader import EnhancedTranscriptLoader
from src.processor.transcript_processor import TranscriptProcessor

# Constants - Bach-inspired mathematical patterns
GOLDEN_RATIO = 1.618033988749895
FIBONACCI_SEQUENCE = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

def generate_sample_indices(length: int, method: str = "fibonacci", ratio: float = GOLDEN_RATIO) -> List[int]:
    """
    Generate sample indices using mathematical patterns.
    
    Args:
        length: Length of the sequence to sample from
        method: Sampling method ('fibonacci', 'golden_ratio', or 'wavelet')
        ratio: Ratio for golden ratio sampling
        
    Returns:
        List of indices for sampling
    """
    if length <= 10:
        # If the sequence is short, use all indices
        return list(range(length))
    
    if method == "fibonacci":
        # Use Fibonacci sequence for sampling
        indices = [i for i in FIBONACCI_SEQUENCE if i < length]
        # Ensure we include the last element
        if indices and indices[-1] < length - 1:
            indices.append(length - 1)
        return indices
    
    elif method == "golden_ratio":
        # Use golden ratio for sampling
        indices = []
        current = 0
        while current < length:
            indices.append(int(current))
            current = current * ratio + 1
        return indices
    
    elif method == "wavelet":
        # Use a wavelet-inspired approach (dyadic sampling)
        indices = [0]  # Start with the first element
        
        # Add dyadic scales (powers of 2)
        scale = 1
        while scale < length:
            for i in range(scale, length, scale * 2):
                indices.append(i)
            scale *= 2
        
        # Ensure we include the last element
        if indices and indices[-1] < length - 1:
            indices.append(length - 1)
            
        # Sort and remove duplicates
        indices = sorted(set(indices))
        return indices
    
    else:
        # Default to linear sampling
        return list(range(0, length, max(1, length // 10)))

def process_transcripts(base_dir: str, 
                       output_dir: str,
                       sampling_method: str = "fibonacci",
                       max_files_per_source: Optional[int] = None):
    """
    Process transcripts using mathematical pattern sampling.
    
    Args:
        base_dir: Base directory containing transcripts
        output_dir: Directory to store output
        sampling_method: Method for sampling ('fibonacci', 'golden_ratio', or 'wavelet')
        max_files_per_source: Maximum files to process per source
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize enhanced transcript loader
    loader = EnhancedTranscriptLoader(base_dir=base_dir)
    
    # Initialize the transcript processor
    processor = TranscriptProcessor()
    
    # Process each source
    source_stats = {}
    total_transcripts = 0
    total_patterns = 0
    
    for source in ["claude", "chatgpt", "grok", "gemini"]:
        logger.info(f"Processing transcripts from {source}...")
        
        # Load transcripts with Fibonacci sampling
        transcripts = loader.load_transcripts(
            source=source, 
            max_files=max_files_per_source,
            sample_by_fibonacci=(sampling_method == "fibonacci")
        )
        
        if not transcripts:
            logger.warning(f"No transcripts found for {source}")
            continue
        
        # Apply appropriate sampling method if not Fibonacci
        if sampling_method != "fibonacci" and len(transcripts) > 10:
            indices = generate_sample_indices(len(transcripts), method=sampling_method)
            logger.info(f"Sampling {len(indices)} out of {len(transcripts)} transcripts using {sampling_method}")
            transcripts = [transcripts[i] for i in indices]
        
        # Process the transcripts
        logger.info(f"Processing {len(transcripts)} transcripts from {source}")
        
        # Process all transcripts at once
        results = processor.process_transcript_batch(transcripts)
        
        # Extract patterns
        patterns = results.get("patterns", {})
        pattern_count = sum(len(p) for p in patterns.values())
        
        # Update statistics
        source_stats[source] = {
            "transcript_count": len(transcripts),
            "pattern_count": pattern_count
        }
        
        total_transcripts += len(transcripts)
        total_patterns += pattern_count
        
        # Save the results
        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"patterns_{source}_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved {pattern_count} patterns from {source} to {output_file}")
    
    # Generate overall pattern report
    pattern_report = processor.generate_pattern_report()
    
    # Add processing metadata
    pattern_report["processing_metadata"] = {
        "timestamp": time.time(),
        "total_transcripts_processed": total_transcripts,
        "total_patterns_extracted": total_patterns,
        "source_statistics": source_stats,
        "sampling_method": sampling_method
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
    print(f"Total transcripts processed: {total_transcripts}")
    print(f"Total patterns extracted: {total_patterns}")
    
    # Print source statistics
    print("\nSource Statistics:")
    for source, stats in source_stats.items():
        print(f"  {source.upper()}: {stats['transcript_count']} transcripts, {stats['pattern_count']} patterns")
    
    print(f"\nPattern report saved to: {report_file}")
    print(f"Visualization data exported to: {viz_data_file}")

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Process transcripts and extract patterns using mathematical sampling")
    
    parser.add_argument(
        "--base-dir",
        default="/home/computeruse/github/palios-taey-nova/transcripts",
        help="Base directory containing transcripts"
    )
    
    parser.add_argument(
        "--output-dir",
        default="/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/patterns",
        help="Directory to store output"
    )
    
    parser.add_argument(
        "--sampling-method",
        choices=["fibonacci", "golden_ratio", "wavelet"],
        default="fibonacci",
        help="Mathematical sampling method to use"
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum files to process per source"
    )
    
    args = parser.parse_args()
    
    # Process transcripts
    process_transcripts(
        base_dir=args.base_dir,
        output_dir=args.output_dir,
        sampling_method=args.sampling_method,
        max_files_per_source=args.max_files
    )