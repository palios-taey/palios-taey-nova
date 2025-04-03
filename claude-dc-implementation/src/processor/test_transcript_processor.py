#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transcript Processor Test Script
-------------------------------
This script tests the EnhancedTranscriptProcessor with various transcript formats
to ensure it correctly handles Claude, ChatGPT, and other AI system outputs.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Import the processor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enhanced_transcript_processor import EnhancedTranscriptProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_transcript_processor")

def test_processor(transcripts_dir: str, max_files: int = 2):
    """
    Test the enhanced transcript processor with various files.
    
    Args:
        transcripts_dir: Directory containing transcripts
        max_files: Maximum number of files to test per source
    """
    processor = EnhancedTranscriptProcessor()
    
    # Define sources to test
    sources = ["claude", "chatgpt", "grok", "gemini"]
    
    # Track results
    results = {
        "total_files": 0,
        "successful_files": 0,
        "failed_files": 0,
        "by_source": {}
    }
    
    for source in sources:
        source_dir = os.path.join(transcripts_dir, source)
        if not os.path.exists(source_dir):
            logger.warning(f"Directory not found for {source}: {source_dir}")
            continue
            
        results["by_source"][source] = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "file_results": []
        }
        
        # Find transcript files
        extensions = [".json", ".txt", ".md"]
        files = []
        
        for ext in extensions:
            source_files = list(Path(source_dir).glob(f"**/*{ext}"))
            files.extend(source_files)
            
        # Limit the number of files
        files = files[:max_files]
        
        # Process each file
        for file_path in files:
            try:
                file_str = str(file_path)
                logger.info(f"Processing {source} file: {file_path}")
                
                # Track this file
                results["total_files"] += 1
                results["by_source"][source]["total"] += 1
                
                # Process the transcript
                transcript = processor.process_transcript(file_str)
                
                # Check if successful
                success = "text" in transcript and transcript["text"] and "error" not in transcript
                
                # Record result
                file_result = {
                    "file": file_str,
                    "success": success,
                    "has_text": "text" in transcript and bool(transcript["text"]),
                    "has_messages": "messages" in transcript and bool(transcript["messages"]),
                    "text_length": len(transcript.get("text", "")),
                    "message_count": len(transcript.get("messages", [])),
                    "error": transcript.get("error", None)
                }
                
                results["by_source"][source]["file_results"].append(file_result)
                
                # Update counts
                if success:
                    results["successful_files"] += 1
                    results["by_source"][source]["successful"] += 1
                    
                    # Try pattern extraction
                    patterns = processor.extract_patterns(transcript)
                    pattern_count = sum(len(p) for p in patterns.values())
                    file_result["pattern_count"] = pattern_count
                    logger.info(f"  Extracted {pattern_count} patterns from {file_str}")
                else:
                    results["failed_files"] += 1
                    results["by_source"][source]["failed"] += 1
                    logger.error(f"  Failed to process {file_str}: {transcript.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results["failed_files"] += 1
                results["by_source"][source]["failed"] += 1
                results["by_source"][source]["file_results"].append({
                    "file": str(file_path),
                    "success": False,
                    "error": str(e)
                })
    
    # Print summary
    logger.info("=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total files processed: {results['total_files']}")
    logger.info(f"Successful: {results['successful_files']} ({results['successful_files']/max(1, results['total_files'])*100:.1f}%)")
    logger.info(f"Failed: {results['failed_files']} ({results['failed_files']/max(1, results['total_files'])*100:.1f}%)")
    logger.info("-" * 50)
    
    for source, source_results in results["by_source"].items():
        total = source_results["total"]
        if total > 0:
            success_rate = source_results["successful"] / total * 100
            logger.info(f"{source.upper()}: {source_results['successful']}/{total} successful ({success_rate:.1f}%)")
            
            # List failed files
            if source_results["failed"] > 0:
                logger.info("  Failed files:")
                for file_result in source_results["file_results"]:
                    if not file_result["success"]:
                        logger.info(f"    - {file_result['file']}: {file_result.get('error', 'Unknown error')}")
    
    logger.info("=" * 50)
    
    # Save results to file
    results_file = "transcript_processor_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Detailed results saved to {results_file}")
    
    return results
            
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the enhanced transcript processor")
    parser.add_argument(
        "--transcripts-dir", 
        default="/home/computeruse/github/palios-taey-nova/transcripts",
        help="Directory containing transcripts"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=2,
        help="Maximum number of files to test per source"
    )
    
    args = parser.parse_args()
    
    # Run the test
    test_processor(args.transcripts_dir, args.max_files)
