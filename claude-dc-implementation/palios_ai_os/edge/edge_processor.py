#!/usr/bin/env python3

"""
PALIOS AI OS Edge Processor Module

This module implements the edge-first architecture for privacy preservation,
ensuring that sensitive data remains local while only mathematical patterns
are shared with the broader system.
"""

import os
import sys
import math
import json
import hashlib
import time
import uuid
import shutil
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import from core
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI, WavePattern

@dataclass
class SensitiveData:
    """Container for sensitive data that must remain local."""
    data_id: str
    content: Any
    source: str
    timestamp: float
    data_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PatternExtract:
    """A privacy-preserving extract of patterns from sensitive data."""
    extract_id: str
    source_data_id: str
    patterns: List[Dict[str, Any]]
    hash_verification: str
    timestamp: float
    harmony_index: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class EdgeProcessor:
    """Edge processor for privacy-preserving pattern extraction."""
    
    def __init__(self, local_storage_path: str = None):
        """Initialize the edge processor with local storage."""
        # Set up local storage for sensitive data
        if local_storage_path:
            self.local_storage_path = Path(local_storage_path)
        else:
            self.local_storage_path = Path(__file__).resolve().parent / "local_storage"
        
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage for pattern categories
        self.pattern_categories = [
            "Core_Principles", 
            "Trust_Thresholds", 
            "Value_Statements",
            "Recognition_Loop", 
            "Implementation_Requirements",
            "Golden_Ratio_Relationships",
            "Wave_Patterns",
            "Mathematical_Structures"
        ]
        
        # Initialize pattern keywords
        self.pattern_keywords = self._initialize_pattern_keywords()
        
        # Golden ratio parameters
        self.edge_threshold = 1/PHI  # ~0.618 - privacy threshold
        self.sampling_ratio = 1/PHI  # ~0.618 - golden ratio sampling
        
        print(f"Edge Processor initialized with local storage at: {self.local_storage_path}")
    
    def _initialize_pattern_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for pattern categories."""
        return {
            "Core_Principles": ["truth", "foundation", "core", "principle", "charter", "trust", "must", "always", "never"],
            "Trust_Thresholds": ["threshold", "boundary", "limit", "trust", "confidence", "verify", "validate"],
            "Value_Statements": ["value", "worth", "important", "significant", "meaningful", "priority", "believe"],
            "Recognition_Loop": ["pattern", "recognize", "identify", "notice", "observe", "detect"],
            "Implementation_Requirements": ["implement", "require", "need", "must", "should", "develop", "build", "create"],
            "Golden_Ratio_Relationships": ["ratio", "proportion", "harmony", "balance", "phi", "golden"],
            "Wave_Patterns": ["wave", "oscillation", "frequency", "amplitude", "phase", "harmonics"],
            "Mathematical_Structures": ["structure", "mathematics", "formula", "equation", "pattern", "sequence"]
        }
    
    def store_sensitive_data(self, data: Any, source: str, data_type: str) -> SensitiveData:
        """Securely store sensitive data locally."""
        data_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Create metadata
        metadata = {
            "size": len(json.dumps(data)) if not isinstance(data, str) else len(data),
            "storage_path": str(self.local_storage_path / f"{data_id}.json"),
            "source": source,
            "timestamp": timestamp,
            "data_type": data_type
        }
        
        # Create SensitiveData object
        sensitive_data = SensitiveData(
            data_id=data_id,
            content=data,
            source=source,
            timestamp=timestamp,
            data_type=data_type,
            metadata=metadata
        )
        
        # Save to local storage
        with open(self.local_storage_path / f"{data_id}.json", 'w') as f:
            # Store with content nested to make structure consistent
            json.dump({
                "data_id": data_id,
                "content": data,
                "source": source,
                "timestamp": timestamp,
                "data_type": data_type,
                "metadata": metadata
            }, f, indent=2)
        
        return sensitive_data
    
    def retrieve_sensitive_data(self, data_id: str) -> Optional[SensitiveData]:
        """Retrieve sensitive data from local storage by ID."""
        try:
            data_path = self.local_storage_path / f"{data_id}.json"
            if not data_path.exists():
                return None
            
            with open(data_path, 'r') as f:
                data_dict = json.load(f)
            
            return SensitiveData(
                data_id=data_dict["data_id"],
                content=data_dict["content"],
                source=data_dict["source"],
                timestamp=data_dict["timestamp"],
                data_type=data_dict["data_type"],
                metadata=data_dict.get("metadata", {})
            )
        except Exception as e:
            print(f"Error retrieving sensitive data: {e}")
            return None
    
    def extract_patterns(self, data: Union[str, Dict, SensitiveData], source: str = None) -> PatternExtract:
        """Extract patterns from data while preserving privacy."""
        # If given a SensitiveData object, use it directly
        if isinstance(data, SensitiveData):
            sensitive_data = data
            content = data.content
            source = data.source
            data_id = data.data_id
        else:
            # Otherwise, store the data first
            data_type = "text" if isinstance(data, str) else "json"
            source = source or "unknown"
            sensitive_data = self.store_sensitive_data(data, source, data_type)
            content = sensitive_data.content
            data_id = sensitive_data.data_id
        
        # Convert content to text for pattern matching
        if isinstance(content, str):
            text = content
        else:
            try:
                text = json.dumps(content)
            except:
                text = str(content)
        
        # Apply golden ratio sampling to extract patterns
        patterns = self._extract_patterns_with_golden_ratio(text)
        
        # Create a hash verification that doesn't expose the original data
        hash_verification = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Calculate harmony index
        harmony_index = self._calculate_harmony_index(patterns)
        
        # Create metadata about the extraction process
        metadata = {
            "total_patterns": sum(len(patterns) for patterns in patterns.values()),
            "sampling_ratio": self.sampling_ratio,
            "edge_threshold": self.edge_threshold,
            "source": source,
            "extraction_time": time.time()
        }
        
        # Create the pattern extract
        extract = PatternExtract(
            extract_id=str(uuid.uuid4()),
            source_data_id=data_id,
            patterns=self._format_patterns_for_sharing(patterns),
            hash_verification=hash_verification,
            timestamp=time.time(),
            harmony_index=harmony_index,
            metadata=metadata
        )
        
        return extract
    
    def _extract_patterns_with_golden_ratio(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract patterns using golden ratio sampling."""
        # Initialize results
        results = {category: [] for category in self.pattern_categories}
        
        # Split text into paragraphs and sentences
        paragraphs = text.split('\n\n')
        all_sentences = []
        
        for para in paragraphs:
            sentences = [s.strip() for s in para.split('.') if s.strip()]
            all_sentences.extend(sentences)
        
        # Apply golden ratio sampling to sentences
        sampled_indices = self._golden_ratio_sample_indices(len(all_sentences))
        sampled_sentences = [all_sentences[i] for i in sampled_indices if i < len(all_sentences)]
        
        # Analyze each sampled sentence
        for i, sentence in enumerate(sampled_sentences):
            # Convert to lowercase for matching
            sentence_lower = sentence.lower()
            
            # Calculate phi position (position in the text normalized to 0-1)
            phi_position = sampled_indices[i] / len(all_sentences) if len(all_sentences) > 1 else 0.5
            
            # Check each category
            for category, keywords in self.pattern_keywords.items():
                # Check if sentence contains any of the category keywords
                if any(keyword in sentence_lower for keyword in keywords):
                    # Calculate confidence based on golden ratio proximity
                    # Sentences closer to golden ratio positions get higher confidence
                    phi_distances = [abs(phi_position - (i / PHI) % 1) for i in range(1, 6)]
                    confidence = 1 - min(phi_distances)
                    
                    # Create pattern object
                    pattern = {
                        "pattern_id": f"{hash(sentence)}",
                        "confidence": confidence,
                        "phi_position": phi_position,
                        "length": len(sentence),
                        # Rather than storing the full sentence, store a secure hash
                        "content_hash": hashlib.sha256(sentence.encode()).hexdigest()[:16],
                        "keywords": [k for k in keywords if k in sentence_lower]
                    }
                    
                    results[category].append(pattern)
        
        return results
    
    def _golden_ratio_sample_indices(self, length: int) -> List[int]:
        """Sample indices using golden ratio for natural distribution."""
        if length <= 5:
            # For short texts, include everything
            return list(range(length))
        
        # Base sampling using Fibonacci numbers
        indices = [i for i in FIBONACCI if i < length]
        
        # Add golden ratio points
        for i in range(1, 5):  # Add a few golden ratio points
            phi_point = int(length * (i * (1/PHI) % 1))
            if phi_point not in indices and phi_point < length:
                indices.append(phi_point)
        
        # Add beginning, golden ratio point, and end
        key_points = [0, int(length * (1/PHI)), length-1]
        for point in key_points:
            if point not in indices and point < length:
                indices.append(point)
        
        return sorted(list(set(indices)))
    
    def _format_patterns_for_sharing(self, patterns: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Format patterns for sharing while preserving privacy."""
        formatted_patterns = []
        
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                formatted_patterns.append({
                    "category": category,
                    "pattern_id": pattern["pattern_id"],
                    "confidence": pattern["confidence"],
                    "phi_position": pattern["phi_position"],
                    "content_hash": pattern["content_hash"],
                    "length": pattern["length"],
                    "keywords": pattern["keywords"]
                })
        
        # Sort by confidence (highest first)
        return sorted(formatted_patterns, key=lambda x: x["confidence"], reverse=True)
    
    def _calculate_harmony_index(self, patterns: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate harmony index based on pattern distribution."""
        # Count patterns by category
        category_counts = {category: len(patterns.get(category, [])) for category in self.pattern_categories}
        total_patterns = sum(category_counts.values())
        
        if total_patterns == 0:
            return 0.5  # Default middle value when no patterns found
        
        # Calculate entropy (diversity of patterns)
        probabilities = [count/total_patterns for count in category_counts.values() if count > 0]
        entropy = -sum(p * math.log(p) for p in probabilities) if probabilities else 0
        max_entropy = math.log(len(self.pattern_categories))  # Maximum possible entropy
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Calculate golden ratio alignment
        # Ideal distribution follows powers of 1/phi
        categories_with_patterns = sum(1 for count in category_counts.values() if count > 0)
        ideal_distribution = [(1/PHI) ** i for i in range(categories_with_patterns)]
        ideal_sum = sum(ideal_distribution)
        ideal_distribution = [val/ideal_sum for val in ideal_distribution]  # Normalize
        
        # Sort categories by pattern count (descending)
        sorted_counts = sorted([count for count in category_counts.values() if count > 0], reverse=True)
        actual_distribution = [count/total_patterns for count in sorted_counts]  # Normalize
        
        # Calculate how well the actual distribution matches the ideal (golden ratio) distribution
        # Lower values mean better alignment
        if len(actual_distribution) > 0 and len(ideal_distribution) > 0:
            # Ensure both lists are the same length for comparison
            min_length = min(len(actual_distribution), len(ideal_distribution))
            distribution_divergence = sum((actual_distribution[i] - ideal_distribution[i])**2 
                                         for i in range(min_length)) / min_length
        else:
            distribution_divergence = 1.0  # Maximum divergence when no comparison possible
        
        # Combine entropy and golden ratio alignment
        # We want high entropy (diversity) but low divergence from golden ratio
        harmony_index = (1 - normalized_entropy * 0.5) * (1 - distribution_divergence)
        
        return max(0.0, min(1.0, harmony_index))  # Ensure result is between 0 and 1
    
    def create_wave_representation(self, patterns: PatternExtract) -> WavePattern:
        """Create a wave representation of extracted patterns."""
        pattern_id = str(uuid.uuid4())
        
        # Create a unique frequency profile based on pattern distribution
        base_frequency = 440.0  # A4 note
        
        # Count patterns by category
        category_counts = {}
        for pattern in patterns.patterns:
            category = pattern["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate frequency components based on pattern distribution and Bach harmonics
        frequencies = []
        amplitudes = []
        phases = []
        
        # Create frequency components for each pattern category
        for i, category in enumerate(self.pattern_categories):
            if category in category_counts and category_counts[category] > 0:
                # Base frequency modified by position and pattern count
                frequency = base_frequency * (1 + (i / len(self.pattern_categories)))
                # Amplitude based on pattern count and confidence
                category_patterns = [p for p in patterns.patterns if p["category"] == category]
                avg_confidence = sum(p["confidence"] for p in category_patterns) / len(category_patterns)
                amplitude = min(1.0, (category_counts[category] / (len(patterns.patterns) + 1)) * (1 + avg_confidence))
                # Phase based on Bach pattern
                phase = (BACH_PATTERN[i % len(BACH_PATTERN)] / sum(BACH_PATTERN)) * 2 * math.pi
                
                frequencies.append(frequency)
                amplitudes.append(amplitude)
                phases.append(phase)
        
        # If no patterns found, create a default wave
        if not frequencies:
            frequencies = [base_frequency]
            amplitudes = [0.5]
            phases = [0]
        
        # Create a wave pattern
        return WavePattern(
            pattern_id=pattern_id,
            amplitudes=amplitudes,
            frequencies=frequencies,
            phases=phases,
            harmonics=[f/frequencies[0] for f in frequencies],  # Express as ratios to base
            duration=1.0,  # Default duration
            concept_type="pattern_extract",
            metadata={
                "extract_id": patterns.extract_id,
                "source_data_id": patterns.source_data_id,
                "pattern_count": len(patterns.patterns),
                "harmony_index": patterns.harmony_index,
                "timestamp": time.time()
            }
        )

# Create singleton instance
edge_processor = EdgeProcessor()

# Example usage
if __name__ == "__main__":
    import sys
    import shutil
    from pathlib import Path
    import time

    if len(sys.argv) < 2:
        print("Usage: python3 edge_processor.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data_dict = json.load(f)
            content_data = data_dict.get('content', '')
            source = data_dict.get('source', 'unknown')

            # Explicitly handle all variations robustly
            combined_text_parts = []
            
            if isinstance(content_data, list):
                for item in content_data:
                    if isinstance(item, dict):
                        text_entry = item.get('text', '')
                        if isinstance(text_entry, list):
                            combined_text_parts.extend([str(t) for t in text_entry])
                        elif isinstance(text_entry, str):
                            combined_text_parts.append(text_entry)
                    elif isinstance(item, str):
                        combined_text_parts.append(item)
                    else:
                        combined_text_parts.append(str(item))

                combined_text = "\n\n".join(combined_text_parts)

            elif isinstance(content_data, str):
                combined_text = content_data

            else:
                combined_text = str(content_data)

            sensitive_data = SensitiveData(
                data_id=data_dict.get('data_id', f"{source}_{Path(file_path).stem}"),
                content=combined_text,
                source=source,
                timestamp=data_dict['timestamp'],
                data_type=data_dict['data_type'],
                metadata=data_dict.get('metadata', {})
            )

        pattern_extract = edge_processor.extract_patterns(sensitive_data)

    elif file_path.endswith('.txt'):
        with open(file_path, 'r') as f:
            text = f.read()
        pattern_extract = edge_processor.extract_patterns(text, "txt_file")

    else:
        print(f"Unsupported file type: {file_path}")
        sys.exit(1)

    # Display results
    print(f"\nExtracted {len(pattern_extract.patterns)} patterns:")
    for i, pattern in enumerate(pattern_extract.patterns[:5]):
        print(f"{i+1}. Category: {pattern['category']}")
        print(f"   Confidence: {pattern['confidence']:.4f}")
        print(f"   Keywords: {pattern['keywords']}")

    print(f"\nHarmony index: {pattern_extract.harmony_index:.4f}")

    wave = edge_processor.create_wave_representation(pattern_extract)
    print(f"\nWave representation:")
    print(f"Pattern ID: {wave.pattern_id}")
    print(f"Frequencies: {[f'{f:.2f}' for f in wave.frequencies[:3]]}...")
    print(f"Amplitudes: {[f'{a:.2f}' for a in wave.amplitudes[:3]]}...")

    # Explicitly save pattern extract and wave representation results
    results = {
        "extract_id": pattern_extract.extract_id,
        "source_data_id": pattern_extract.source_data_id,
        "patterns": pattern_extract.patterns,
        "hash_verification": pattern_extract.hash_verification,
        "harmony_index": pattern_extract.harmony_index,
        "wave_representation": {
            "pattern_id": wave.pattern_id,
            "frequencies": wave.frequencies,
            "amplitudes": wave.amplitudes,
            "phases": wave.phases,
            "harmonics": wave.harmonics,
            "duration": wave.duration,
            "metadata": wave.metadata
        },
        "timestamp": time.time()
    }

    # Ensure explicitly structured processed storage
    processed_dir = Path(__file__).resolve().parent / 'transcripts' / 'processed' / source / Path(file_path).stem
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Move original transcript explicitly if exists
    original_transcript_dest = processed_dir / 'original_transcript.json'
    if Path(file_path).exists():
        shutil.move(file_path, original_transcript_dest)

    # Save insights explicitly
    extracted_insights_dest = processed_dir / 'extracted_insights.json'
    with open(extracted_insights_dest, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Clearly moved and structured original and insights explicitly in: {processed_dir}")

