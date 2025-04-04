import math
import re
import numpy as np
from typing import List, Dict, Any, Optional, Union
from collections import Counter
import pandas as pd
from scipy import signal

# Golden ratio - our fundamental constant
PHI = (1 + math.sqrt(5)) / 2

class PatternExtractor:
    """Extract mathematical patterns from text using Bach-inspired methods.
    
    This class implements wave-based pattern recognition, treating mathematical
    patterns as the essence of ideas rather than mere representations.
    """
    
    def __init__(self):
        # Initialize with Bach's musical ratios
        self.bach_ratios = [1, 4/3, 3/2, 5/3, 2]
        self.fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        self.pattern_categories = [
            "Core_Principles", 
            "Trust_Thresholds", 
            "Value_Statements",
            "Recognition_Loop", 
            "Implementation_Requirements",
            "Golden_Ratio_Relationships"
        ]
        
    def extract_patterns(self, text: str) -> Dict[str, Any]:
        """Extract all patterns from text."""
        # Break text into natural segments
        segments = self._segment_text(text)
        
        # Apply wavelet transform to identify patterns
        wave_patterns = self._apply_wavelet_transform(segments)
        
        # Categorize patterns
        categorized = self._categorize_patterns(wave_patterns, segments)
        
        # Apply golden ratio sampling to select most important patterns
        sampled = self._golden_ratio_sample(categorized)
        
        return {
            "pattern_counts": {cat: len(patterns) for cat, patterns in categorized.items()},
            "sampled_patterns": sampled,
            "harmony_index": self._calculate_harmony_index(categorized)
        }
    
    def _segment_text(self, text: str) -> List[str]:
        """Segment text into natural chunks using sentence and paragraph boundaries."""
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        segments = []
        for para in paragraphs:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            segments.extend(sentences)
        
        return [s for s in segments if s.strip()]
    
    def _apply_wavelet_transform(self, segments: List[str]) -> np.ndarray:
        """Apply wavelet transform to identify wave patterns in text."""
        # Create numerical representation of text
        # This is a simplified version - in production this would be more sophisticated
        
        # Convert text to numerical values using character frequencies
        values = []
        for segment in segments:
            # Count character frequencies
            char_freq = Counter(segment.lower())
            # Create a numerical value from frequency distribution
            segment_value = sum(char_freq[c] * (ord(c) % 32) for c in char_freq) / (len(segment) or 1)
            values.append(segment_value)
        
        # Convert to numpy array
        signal_array = np.array(values)
        
        # Apply wavelet transform if we have enough data
        if len(signal_array) >= 10:
            # Use wavelet transform to find patterns
            coeffs = signal.cwt(signal_array, signal.ricker, np.arange(1, min(10, len(signal_array))))
            return coeffs
        else:
            # Not enough data for wavelet transform, return raw signal
            return signal_array.reshape(1, -1)
    
    def _categorize_patterns(self, wave_patterns: np.ndarray, segments: List[str]) -> Dict[str, List[Dict]]:
        """Categorize patterns based on wave characteristics."""
        results = {category: [] for category in self.pattern_categories}
        
        # Simple categorization based on keywords for demonstration
        # In production, this would use more sophisticated pattern matching
        
        keywords = {
            "Core_Principles": ["truth", "foundation", "core", "principle", "charter", "trust"],
            "Trust_Thresholds": ["threshold", "boundary", "limit", "trust", "confidence"],
            "Value_Statements": ["value", "worth", "important", "significant", "meaningful"],
            "Recognition_Loop": ["pattern", "recognize", "identify", "notice", "observe"],
            "Implementation_Requirements": ["implement", "require", "need", "must", "should", "develop"],
            "Golden_Ratio_Relationships": ["ratio", "proportion", "harmony", "balance", "phi", "golden"]
        }
        
        # Analyze each segment
        for i, segment in enumerate(segments):
            segment_lower = segment.lower()
            
            # Check each category
            for category, category_keywords in keywords.items():
                # Check if segment contains any category keywords
                if any(keyword in segment_lower for keyword in category_keywords):
                    # Calculate confidence based on pattern strength
                    if wave_patterns.ndim > 1 and i < wave_patterns.shape[1]:
                        # Use wavelet coefficients if available
                        pattern_strength = np.max(np.abs(wave_patterns[:, i])) / 10
                    else:
                        pattern_strength = 0.5  # Default value
                    
                    # Normalize confidence between 0 and 1
                    confidence = min(max(pattern_strength, 0), 1)
                    
                    # Add to results
                    results[category].append({
                        "text": segment,
                        "confidence": confidence,
                        "position": i,
                        "segment_length": len(segment)
                    })
        
        return results
    
    def _golden_ratio_sample(self, categorized: Dict[str, List[Dict]]) -> List[Dict]:
        """Sample patterns using golden ratio to identify most significant ones."""
        all_patterns = []
        
        for category, patterns in categorized.items():
            if not patterns:
                continue
                
            # Sort by confidence
            sorted_patterns = sorted(patterns, key=lambda x: x["confidence"], reverse=True)
            
            # Apply golden ratio sampling
            samples = []
            if len(sorted_patterns) > 0:
                # Take at least one pattern
                samples.append(sorted_patterns[0])
                
                # If we have more patterns, use golden ratio positions
                if len(sorted_patterns) > 1:
                    for i in range(1, min(3, len(sorted_patterns))):
                        phi_position = int(i * PHI) % len(sorted_patterns)
                        if sorted_patterns[phi_position] not in samples:
                            samples.append(sorted_patterns[phi_position])
            
            # Add category to each pattern and add to final list
            for pattern in samples:
                pattern["category"] = category
                all_patterns.append(pattern)
        
        # Return top patterns, prioritizing higher confidence
        return sorted(all_patterns, key=lambda x: x["confidence"], reverse=True)[:5]
    
    def _calculate_harmony_index(self, categorized: Dict[str, List[Dict]]) -> float:
        """Calculate overall harmony index based on pattern distribution."""
        # Count patterns in each category
        counts = [len(patterns) for category, patterns in categorized.items()]
        
        if not counts or sum(counts) == 0:
            return 0
        
        # Calculate entropy of distribution
        probabilities = [count/sum(counts) for count in counts]
        entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probabilities)
        
        # Calculate how close the distribution is to the golden ratio
        ideal_distribution = [PHI ** -i for i in range(len(counts))]
        ideal_distribution = [id/sum(ideal_distribution) for id in ideal_distribution]
        
        # Calculate distance from ideal (golden ratio) distribution
        distance = sum((a-b)**2 for a, b in zip(probabilities, ideal_distribution))
        
        # Harmony index: balance of entropy and golden ratio alignment
        harmony = (1 - distance) * (1 - entropy/math.log(len(counts))) if len(counts) > 1 else 1
        
        return max(0, min(1, harmony))

# Create singleton instance
extractor = PatternExtractor()