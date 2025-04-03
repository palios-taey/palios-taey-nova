#!/bin/bash
# install-enhanced-processor.sh
# This script installs the Enhanced Transcript Processor into the claude-dc-implementation directory

echo "Installing Enhanced Transcript Processor..."
echo "========================================"

# Define the paths
REPO_DIR="/home/computeruse/github/palios-taey-nova"
IMPL_DIR="${REPO_DIR}/claude-dc-implementation"
PROCESSOR_DIR="${IMPL_DIR}/src/processor"

# Make sure the processor directory exists
mkdir -p "${PROCESSOR_DIR}"

# Copy the new processor files
cp ./enhanced_transcript_processor.py "${PROCESSOR_DIR}/"
cp ./test_transcript_processor.py "${PROCESSOR_DIR}/"

# Make them executable
chmod +x "${PROCESSOR_DIR}/enhanced_transcript_processor.py"
chmod +x "${PROCESSOR_DIR}/test_transcript_processor.py"

# Create an importer file to maintain compatibility with existing code
cat > "${PROCESSOR_DIR}/transcript_processor_enhanced.py" << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transcript Processor Enhanced - Compatibility Module
---------------------------------------------------
This module provides backward compatibility with the original transcript processor
while using the enhanced version underneath.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .enhanced_transcript_processor import EnhancedTranscriptProcessor

class TranscriptProcessor:
    """
    Compatibility class that wraps the EnhancedTranscriptProcessor
    to maintain the same interface as the original TranscriptProcessor.
    """
    
    def __init__(self):
        """Initialize the processor."""
        self.enhanced_processor = EnhancedTranscriptProcessor()
        self.patterns = defaultdict(list)
        self.metrics = {
            "total_patterns": 0,
            "pattern_counts": {},
            "source_counts": {},
            "confidence_metrics": {}
        }
        
    def process_transcript(self, transcript: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process a transcript using the enhanced processor.
        
        Args:
            transcript: Transcript data
            
        Returns:
            Dictionary of patterns by type
        """
        return self.enhanced_processor.extract_patterns(transcript)
        
    def process_transcript_batch(self, transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of transcripts.
        
        Args:
            transcripts: List of transcript data
            
        Returns:
            Dictionary containing patterns and metrics
        """
        all_patterns = defaultdict(list)
        
        for transcript in transcripts:
            patterns = self.process_transcript(transcript)
            
            # Merge patterns
            for pattern_type, pattern_list in patterns.items():
                all_patterns[pattern_type].extend(pattern_list)
                
                # Update metrics
                if pattern_type not in self.metrics["pattern_counts"]:
                    self.metrics["pattern_counts"][pattern_type] = 0
                self.metrics["pattern_counts"][pattern_type] += len(pattern_list)
                
                # Update source counts
                source = transcript.get("source", "unknown")
                if source not in self.metrics["source_counts"]:
                    self.metrics["source_counts"][source] = 0
                self.metrics["source_counts"][source] += len(pattern_list)
                
                # Store patterns for later use
                self.patterns[pattern_type].extend(pattern_list)
        
        # Update total count
        pattern_count = sum(len(patterns) for patterns in all_patterns.values())
        self.metrics["total_patterns"] += pattern_count
        
        return {
            "patterns": dict(all_patterns),
            "metrics": {
                "total_patterns": pattern_count,
                "pattern_counts": {k: len(v) for k, v in all_patterns.items()},
                "processed_transcripts": len(transcripts)
            }
        }
    
    def generate_pattern_report(self) -> Dict[str, Any]:
        """
        Generate a report of all extracted patterns.
        
        Returns:
            Dictionary containing pattern statistics
        """
        # Calculate frequency distribution
        total_patterns = sum(len(patterns) for patterns in self.patterns.values())
        frequency_distribution = {}
        
        if total_patterns > 0:
            for pattern_type, pattern_list in self.patterns.items():
                frequency_distribution[pattern_type] = len(pattern_list) / total_patterns
        
        # Find top patterns by confidence
        all_patterns = []
        for pattern_list in self.patterns.values():
            all_patterns.extend(pattern_list)
            
        # Sort by confidence (descending)
        top_patterns = sorted(all_patterns, key=lambda p: p.get("confidence", 0), reverse=True)[:10]
        
        return {
            "total_patterns": total_patterns,
            "pattern_count": {k: len(v) for k, v in self.patterns.items()},
            "top_patterns": top_patterns,
            "frequency_distribution": frequency_distribution,
            "timestamp": import time; time.time()
        }
    
    def export_for_visualization(self, output_file: str) -> None:
        """
        Export pattern data for visualization.
        
        Args:
            output_file: Path to save the visualization data
        """
        import json
        
        # Prepare visualization data
        viz_data = {
            "patterns_by_type": dict(self.patterns),
            "metrics": self.metrics,
            "timestamp": import time; time.time()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(viz_data, f, indent=2)
            
        logging.info(f"Visualization data exported to {output_file}")
EOF

# Create a backup of the original processor
if [ -f "${PROCESSOR_DIR}/transcript_processor.py" ]; then
    echo "Creating backup of original transcript processor..."
    cp "${PROCESSOR_DIR}/transcript_processor.py" "${PROCESSOR_DIR}/transcript_processor.py.bak"
    echo "Backup created at ${PROCESSOR_DIR}/transcript_processor.py.bak"
fi

# Create a runner script to test the processor
cat > "${IMPL_DIR}/test_enhanced_processor.py" << 'EOF'
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
EOF

# Make the test script executable
chmod +x "${IMPL_DIR}/test_enhanced_processor.py"

echo "Installation complete!"
echo "You can now test the enhanced processor with:"
echo "  cd ${IMPL_DIR}"
echo "  python3 test_enhanced_processor.py"
echo ""
echo "To integrate with the main pattern processing pipeline:"
echo "  1. Update process_transcripts.py to use the new processor"
echo "  2. Run the processing script with the enhanced processor"
echo ""
