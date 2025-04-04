#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bach-Inspired Mathematical Router
--------------------------------
This module implements a pattern-based router that uses mathematical principles
inspired by Bach's compositions to route messages to the most appropriate AI system.

The router uses golden ratio relationships, pattern recognition, and harmonious
modular design to create an intelligent routing system.
"""

import os
import json
import math
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

# Import local modules
from src.processor.transcript_processor_enhanced import TranscriptProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bach_router")

# Constants
GOLDEN_RATIO = 1.618033988749895
PHI_INVERSE = 0.6180339887498949
AI_SYSTEMS = ["claude", "chatgpt", "grok", "gemini"]

class BachRouter:
    """Router that uses Bach-inspired mathematical principles for message routing."""
    
    def __init__(self, patterns_dir: Optional[str] = None):
        """
        Initialize the Bach router.
        
        Args:
            patterns_dir: Directory containing pattern files (default: data/patterns)
        """
        self.processor = TranscriptProcessor()
        self.patterns_dir = patterns_dir or os.path.join(os.getcwd(), "data", "patterns")
        self.ai_capabilities = self._initialize_ai_capabilities()
        self.patterns = self._load_patterns()
        self.pattern_vectors = self._compute_pattern_vectors()
        self.routing_history = []
        
        logger.info(f"Bach router initialized with {sum(len(p) for p in self.patterns.values())} patterns")
    
    def _initialize_ai_capabilities(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize AI capabilities based on their strengths.
        
        Returns:
            Dictionary mapping AI systems to their capabilities
        """
        capabilities = {
            "claude": {
                "Implementation_Requirements": 0.9,
                "Core_Principles": 0.95,
                "Golden_Ratio_Relationships": 0.85,
                "Trust_Thresholds": 0.9,
                "Value_Statements": 0.95,
                "Recognition_Loop": 0.8
            },
            "chatgpt": {
                "Implementation_Requirements": 0.95,
                "Core_Principles": 0.8,
                "Golden_Ratio_Relationships": 0.75,
                "Trust_Thresholds": 0.8,
                "Value_Statements": 0.85,
                "Recognition_Loop": 0.85
            },
            "grok": {
                "Implementation_Requirements": 0.8,
                "Core_Principles": 0.75,
                "Golden_Ratio_Relationships": 0.9,
                "Trust_Thresholds": 0.75,
                "Value_Statements": 0.7,
                "Recognition_Loop": 0.9
            },
            "gemini": {
                "Implementation_Requirements": 0.85,
                "Core_Principles": 0.8,
                "Golden_Ratio_Relationships": 0.8,
                "Trust_Thresholds": 0.85,
                "Value_Statements": 0.8,
                "Recognition_Loop": 0.8
            }
        }
        
        # Apply golden ratio modulation to create harmonious relationships
        for ai, pattern_capabilities in capabilities.items():
            keys = list(pattern_capabilities.keys())
            for i, key in enumerate(keys):
                # Apply a subtle golden ratio influence
                if i > 0:
                    prev_key = keys[i-1]
                    ideal_ratio = 1 - (i % 2) * (PHI_INVERSE - 0.5)  # Oscillate around PHI and PHI_INVERSE
                    pattern_capabilities[key] = min(1.0, pattern_capabilities[prev_key] * ideal_ratio + 0.05)
        
        return capabilities
    
    def _load_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load patterns from pattern files.
        
        Returns:
            Dictionary of patterns by type
        """
        all_patterns = defaultdict(list)
        report_file = os.path.join(self.patterns_dir, "pattern_report.json")
        
        try:
            # First, try to load the pattern report
            if os.path.exists(report_file):
                with open(report_file, 'r') as f:
                    report = json.load(f)
                    
                    # Extract top patterns
                    if "top_patterns" in report:
                        for pattern in report["top_patterns"]:
                            pattern_type = pattern.get("pattern_type", "unknown")
                            all_patterns[pattern_type].append(pattern)
            
            # Then, load individual pattern files
            pattern_files = list(Path(self.patterns_dir).glob("patterns_*.json"))
            for file_path in pattern_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                        if "patterns" in data and isinstance(data["patterns"], dict):
                            # Extract patterns
                            for pattern_type, patterns in data["patterns"].items():
                                all_patterns[pattern_type].extend(patterns)
                except Exception as e:
                    logger.error(f"Error loading pattern file {file_path}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error loading patterns: {str(e)}")
            # Return empty patterns if loading fails
            return defaultdict(list)
        
        # Remove duplicates
        for pattern_type in all_patterns:
            unique_patterns = {}
            for pattern in all_patterns[pattern_type]:
                # Create a hash of the text for deduplication
                if "text" in pattern:
                    import hashlib
                    text_hash = hashlib.md5(pattern["text"].encode()).hexdigest()
                    if text_hash not in unique_patterns:
                        unique_patterns[text_hash] = pattern
            
            all_patterns[pattern_type] = list(unique_patterns.values())
        
        return dict(all_patterns)
    
    def _compute_pattern_vectors(self) -> Dict[str, np.ndarray]:
        """
        Compute vector representations for each pattern type.
        
        Returns:
            Dictionary mapping pattern types to their vector representations
        """
        pattern_vectors = {}
        
        # For each pattern type, compute a characteristic vector
        for pattern_type, patterns in self.patterns.items():
            # Use simple statistics for now
            confidence_mean = np.mean([p.get("confidence", 0.5) for p in patterns]) if patterns else 0.5
            pattern_count = len(patterns)
            
            # Create a simple vector representation
            vector = np.array([
                confidence_mean,
                min(1.0, pattern_count / 10),  # Normalize count
                GOLDEN_RATIO * (1 if "golden" in pattern_type.lower() else PHI_INVERSE),  # Apply golden ratio influence
                sum(1 for p in patterns if p.get("source") == "claude") / max(1, pattern_count),
                sum(1 for p in patterns if p.get("source") == "chatgpt") / max(1, pattern_count),
                sum(1 for p in patterns if p.get("source") == "grok") / max(1, pattern_count),
                sum(1 for p in patterns if p.get("source") == "gemini") / max(1, pattern_count)
            ])
            
            pattern_vectors[pattern_type] = vector
        
        return pattern_vectors
    
    def extract_message_patterns(self, message: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract patterns from a message.
        
        Args:
            message: The message to extract patterns from
            
        Returns:
            Dictionary of extracted patterns by type
        """
        # Create a transcript-like object
        transcript = {"text": message, "source": "user"}
        
        # Use the processor to extract patterns
        return self.processor.process_transcript(transcript)
    
    def match_patterns(self, message_patterns: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """
        Match message patterns to AI capabilities.
        
        Args:
            message_patterns: Patterns extracted from the message
            
        Returns:
            Dictionary mapping AI systems to match scores
        """
        # Calculate match scores for each AI system
        match_scores = {ai: 0.0 for ai in AI_SYSTEMS}
        
        if not message_patterns:
            # No patterns found, return equal scores
            return {ai: 1.0 / len(AI_SYSTEMS) for ai in AI_SYSTEMS}
        
        # Extract pattern types from the message
        pattern_types = set(message_patterns.keys())
        
        # Calculate score for each AI based on its capabilities
        for ai in AI_SYSTEMS:
            score = 0.0
            
            # Score based on capability for each pattern type
            for pattern_type in pattern_types:
                # Get AI's capability for this pattern type
                capability = self.ai_capabilities.get(ai, {}).get(pattern_type, 0.5)
                
                # Get pattern count and confidence
                patterns = message_patterns.get(pattern_type, [])
                pattern_count = len(patterns)
                
                # Calculate weighted score
                if pattern_count > 0:
                    avg_confidence = sum(p.get("confidence", 0.5) for p in patterns) / pattern_count
                    type_score = capability * avg_confidence * pattern_count
                    
                    # Apply golden ratio modulation
                    type_score *= 1 + (0.1 * math.sin(GOLDEN_RATIO * pattern_count))
                    
                    score += type_score
            
            match_scores[ai] = score
        
        # Normalize scores
        total_score = sum(match_scores.values())
        if total_score > 0:
            for ai in match_scores:
                match_scores[ai] /= total_score
        else:
            # If all scores are 0, return equal scores
            for ai in match_scores:
                match_scores[ai] = 1.0 / len(AI_SYSTEMS)
        
        return match_scores
    
    def route_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, float, Dict[str, Any]]:
        """
        Route a message to the most appropriate AI system.
        
        Args:
            message: The message to route
            context: Optional context information
            
        Returns:
            Tuple of (selected AI, confidence, routing_info)
        """
        # Extract patterns from the message
        message_patterns = self.extract_message_patterns(message)
        
        # Apply context if available
        if context:
            message_patterns = self._apply_context_to_patterns(message_patterns, context)
        
        # Match patterns to AI capabilities
        match_scores = self.match_patterns(message_patterns)
        
        # Select the best AI
        selected_ai = max(match_scores, key=match_scores.get)
        confidence = match_scores[selected_ai]
        
        # Create routing info
        routing_info = {
            "match_scores": match_scores,
            "patterns": message_patterns,
            "timestamp": time.time(),
            "context_applied": bool(context)
        }
        
        # Log the routing decision
        logger.info(f"Routed message to {selected_ai} with confidence {confidence:.2f}")
        
        # Track the routing history
        self.routing_history.append({
            "selected_ai": selected_ai,
            "confidence": confidence,
            "timestamp": time.time(),
            "pattern_count": sum(len(patterns) for patterns in message_patterns.values())
        })
        
        return selected_ai, confidence, routing_info
    
    def _apply_context_to_patterns(self, patterns: Dict[str, List[Dict[str, Any]]], context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Apply context information to patterns.
        
        Args:
            patterns: Dictionary of patterns by type
            context: Context information
            
        Returns:
            Updated patterns
        """
        # Clone patterns to avoid modifying the original
        updated_patterns = defaultdict(list)
        
        for pattern_type, pattern_list in patterns.items():
            updated_patterns[pattern_type] = pattern_list.copy()
        
        # Apply context-based adjustments
        
        # 1. Use conversation history
        if "conversation_history" in context:
            history = context["conversation_history"]
            
            # Check for AI mentions in history
            for ai in AI_SYSTEMS:
                ai_mentions = sum(1 for msg in history if ai.lower() in msg.get("content", "").lower())
                
                if ai_mentions > 0:
                    # Create a new pattern for mentioned AIs
                    updated_patterns["AI_Preference"].append({
                        "text": f"Previous interaction with {ai}",
                        "source": "context",
                        "confidence": min(0.9, 0.5 + (ai_mentions * 0.1)),
                        "signal_word": ai
                    })
        
        # 2. Use user preferences
        if "user_preferences" in context and "preferred_ai" in context["user_preferences"]:
            preferred_ai = context["user_preferences"]["preferred_ai"]
            
            if preferred_ai in AI_SYSTEMS:
                updated_patterns["User_Preference"].append({
                    "text": f"User prefers {preferred_ai}",
                    "source": "context",
                    "confidence": 0.9,
                    "signal_word": "preference"
                })
        
        # 3. Apply golden ratio modulation to pattern confidence
        pattern_count = sum(len(patterns) for patterns in updated_patterns.values())
        golden_factor = PHI_INVERSE + (GOLDEN_RATIO - PHI_INVERSE) * math.sin(pattern_count / 10)
        
        for pattern_type in updated_patterns:
            for pattern in updated_patterns[pattern_type]:
                if "confidence" in pattern:
                    pattern["confidence"] = min(0.99, pattern["confidence"] * golden_factor)
        
        return dict(updated_patterns)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about routing decisions.
        
        Returns:
            Dictionary of routing statistics
        """
        if not self.routing_history:
            return {"error": "No routing history available"}
        
        # Calculate statistics
        ai_counts = defaultdict(int)
        ai_confidences = defaultdict(list)
        
        for entry in self.routing_history:
            ai = entry["selected_ai"]
            ai_counts[ai] += 1
            ai_confidences[ai].append(entry["confidence"])
        
        # Create stats
        stats = {
            "total_routes": len(self.routing_history),
            "ai_distribution": {ai: count / len(self.routing_history) for ai, count in ai_counts.items()},
            "average_confidence": {ai: sum(confs) / len(confs) if confs else 0 for ai, confs in ai_confidences.items()},
            "recent_routes": self.routing_history[-5:] if len(self.routing_history) >= 5 else self.routing_history
        }
        
        return stats

# Example usage
if __name__ == "__main__":
    # Create router
    router = BachRouter()
    
    # Test messages
    test_messages = [
        "Can you help me implement a privacy-preserving edge processing system?",
        "What do you think about the golden ratio in interface design?",
        "I'm trying to understand the core principles of the PALIOS-TAEY system.",
        "How can I balance human needs with system capabilities?",
        "I noticed a pattern when we integrated the pattern recognition system."
    ]
    
    print("\nTesting Bach-inspired router with sample messages:")
    print("="*70)
    
    for message in test_messages:
        print(f"\nMessage: {message}")
        selected_ai, confidence, routing_info = router.route_message(message)
        print(f"  Selected AI: {selected_ai} (confidence: {confidence:.2f})")
        print(f"  Match scores: {', '.join([f'{ai}: {score:.2f}' for ai, score in routing_info['match_scores'].items()])}")
        print(f"  Pattern count: {sum(len(patterns) for patterns in routing_info['patterns'].values())}")
    
    # Print routing stats
    print("\nRouting Statistics:")
    print("="*70)
    stats = router.get_routing_stats()
    print(f"Total routes: {stats['total_routes']}")
    print("AI distribution:")
    for ai, dist in stats['ai_distribution'].items():
        print(f"  {ai}: {dist:.2f}")
    print("Average confidence:")
    for ai, conf in stats['average_confidence'].items():
        print(f"  {ai}: {conf:.2f}")
