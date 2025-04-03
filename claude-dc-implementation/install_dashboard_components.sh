#!/bin/bash
# install_dashboard_components.sh
# This script installs the enhanced transcript processor, Bach router, 
# MCP connector, and dashboard UI components

echo "Installing Communication Dashboard Components..."
echo "=============================================="

# Define the paths
REPO_DIR="/home/jesse/projects/palios-taey-nova"
IMPL_DIR="${REPO_DIR}/claude-dc-implementation"
PROCESSOR_DIR="${IMPL_DIR}/src/processor"
DASHBOARD_DIR="${IMPL_DIR}/src/dashboard"

# Make sure the directories exist
mkdir -p "${PROCESSOR_DIR}"
mkdir -p "${DASHBOARD_DIR}"

# 1. Install Enhanced Transcript Processor
echo "Installing Enhanced Transcript Processor..."
cp enhanced_transcript_processor.py "${PROCESSOR_DIR}/"
cp test_transcript_processor.py "${PROCESSOR_DIR}/"

# Create the compatibility layer
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
EOF

# Make the files executable
chmod +x "${PROCESSOR_DIR}/enhanced_transcript_processor.py"
chmod +x "${PROCESSOR_DIR}/test_transcript_processor.py"
chmod +x "${PROCESSOR_DIR}/transcript_processor_enhanced.py"

echo "Enhanced Transcript Processor installed successfully!"

# 2. Install Bach Router
echo "Installing Bach Router..."
cp bach_router.py "${DASHBOARD_DIR}/"
chmod +x "${DASHBOARD_DIR}/bach_router.py"
echo "Bach Router installed successfully!"

# 3. Install MCP Connector
echo "Installing Dashboard MCP Connector..."
cp dashboard_mcp_connector.py "${DASHBOARD_DIR}/"
chmod +x "${DASHBOARD_DIR}/dashboard_mcp_connector.py"
echo "Dashboard MCP Connector installed successfully!"

# 4. Install Dashboard App
echo "Installing Dashboard App..."
cp dashboard_app.py "${IMPL_DIR}/"
chmod +x "${IMPL_DIR}/dashboard_app.py"
echo "Dashboard App installed successfully!"

# 5. Install documentation
echo "Installing Documentation..."
mkdir -p "${IMPL_DIR}/docs"
cp enhanced_processor_docs.md "${IMPL_DIR}/docs/"
cp integration_plan.md "${IMPL_DIR}/docs/"
echo "Documentation installed successfully!"

# 6. Create dashboard runner script
echo "Creating dashboard runner script..."
cat > "${IMPL_DIR}/run_dashboard.sh" << 'EOF'
#!/bin/bash

# Run the communication dashboard
echo "Starting Communication Dashboard..."
streamlit run dashboard_app.py --server.port=8502
EOF

chmod +x "${IMPL_DIR}/run_dashboard.sh"
echo "Dashboard runner script created successfully!"

# 7. Create test script
echo "Creating test script..."
cat > "${IMPL_DIR}/test_components.sh" << 'EOF'
#!/bin/bash

# Test dashboard components
echo "Testing Dashboard Components..."
echo "============================"

# 1. Test Enhanced Transcript Processor
echo "Testing Enhanced Transcript Processor..."
cd "$(dirname "$0")"
python3 -m src.processor.test_transcript_processor
echo ""

# 2. Test Bach Router
echo "Testing Bach Router..."
cd "$(dirname "$0")"
python3 -m src.dashboard.bach_router
echo ""

# 3. Test MCP Connector
echo "Testing MCP Connector..."
cd "$(dirname "$0")"
python3 -m src.dashboard.dashboard_mcp_connector
echo ""

echo "All tests complete!"
EOF

chmod +x "${IMPL_DIR}/test_components.sh"
echo "Test script created successfully!"

echo ""
echo "Installation Complete!"
echo "You can now test the components with:"
echo "  cd ${IMPL_DIR}"
echo "  ./test_components.sh"
echo ""
echo "And run the dashboard with:"
echo "  cd ${IMPL_DIR}"
echo "  ./run_dashboard.sh"
echo ""
echo "Note: Make sure the MCP server is running on port 8001"
echo "before testing the MCP connector or running the dashboard."
