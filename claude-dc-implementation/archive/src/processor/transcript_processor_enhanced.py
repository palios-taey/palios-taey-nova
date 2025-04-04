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
import time

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
            "timestamp": time.time()
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
            "timestamp": time.time()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(viz_data, f, indent=2)
            
        logging.info(f"Visualization data exported to {output_file}")
