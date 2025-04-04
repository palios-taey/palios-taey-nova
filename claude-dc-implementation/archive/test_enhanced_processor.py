#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Enhanced Transcript Processor
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the processor
from src.processor.enhanced_transcript_processor import EnhancedTranscriptProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_enhanced_processor")

def run_test():
    """Run a test of the enhanced processor"""
    # Create processor
    processor = EnhancedTranscriptProcessor()
    logger.info("Enhanced Transcript Processor initialized")
    
    # Define paths to test
    transcripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "transcripts")
    
    if not os.path.exists(transcripts_dir):
        logger.error(f"Transcripts directory not found: {transcripts_dir}")
        logger.info("Looking for transcripts in alternative locations...")
        
        # Try to find transcripts in other locations
        possible_paths = [
            "/home/computeruse/github/palios-taey-nova/transcripts",
            "/home/computeruse/transcripts"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                transcripts_dir = path
                logger.info(f"Found transcripts at: {transcripts_dir}")
                break
        else:
            logger.error("Could not find transcripts directory. Please specify the path:")
            transcripts_dir = input("Path to transcripts: ")
            if not os.path.exists(transcripts_dir):
                logger.error(f"Invalid path: {transcripts_dir}")
                return
    
    # Test with each source
    sources = ["claude", "chatgpt", "grok", "gemini"]
    
    for source in sources:
        source_dir = os.path.join(transcripts_dir, source)
        if not os.path.exists(source_dir):
            logger.warning(f"Directory not found for {source}: {source_dir}")
            continue
            
        logger.info(f"Testing processor with {source} transcripts...")
        
        # Find transcript files
        extensions = [".json", ".txt", ".md"]
        files = []
        
        for ext in extensions:
            source_files = list(Path(source_dir).glob(f"**/*{ext}"))
            files.extend(source_files)
            
        # Limit to 2 files for quick testing
        files = files[:2]
        
        if not files:
            logger.warning(f"No transcript files found for {source}")
            continue
            
        # Process each file
        for file_path in files:
            try:
                file_str = str(file_path)
                logger.info(f"Processing {source} file: {file_path}")
                
                # Process the transcript
                transcript = processor.process_transcript(file_str)
                
                # Check if successful
                success = "text" in transcript and transcript["text"] and "error" not in transcript
                
                if success:
                    logger.info(f"  Success! Extracted {len(transcript.get('text', ''))} chars of text")
                    logger.info(f"  Found {len(transcript.get('messages', []))} messages")
                    
                    # Extract patterns
                    patterns = processor.extract_patterns(transcript)
                    pattern_count = sum(len(p) for p in patterns.values())
                    logger.info(f"  Extracted {pattern_count} patterns")
                else:
                    logger.error(f"  Failed to process {file_str}: {transcript.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
    
    logger.info("Testing complete!")

if __name__ == "__main__":
    run_test()
