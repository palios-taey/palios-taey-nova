import os
import json
import hashlib
import numpy as np
import math
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import uuid

# Golden ratio - our fundamental constant
PHI = (1 + math.sqrt(5)) / 2

@dataclass
class TranscriptMetadata:
    """Metadata about a transcript, without the sensitive content."""
    transcript_id: str
    timestamp: float
    duration: float
    participant_count: int
    topic_hash: str
    pattern_count: int
    pattern_types: Dict[str, int]
    word_count: int
    harmony_index: float

@dataclass
class Pattern:
    """A pattern extracted from a transcript."""
    pattern_id: str
    pattern_type: str
    confidence: float
    hash: str
    phi_position: float
    context_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExtractedPatterns:
    """Patterns extracted from a transcript with metadata."""
    transcript_metadata: TranscriptMetadata
    patterns: List[Pattern]

class EdgeProcessor:
    """Process sensitive data locally, extracting only patterns for cloud transmission.
    
    This class implements the edge-first privacy principle, ensuring that raw
    sensitive data never leaves the local environment while still enabling
    pattern analysis and sharing.
    """
    
    def __init__(self, local_storage_path: str = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/edge/local_storage"):
        self.local_storage_path = local_storage_path
        self.pattern_categories = [
            "Core_Principles", 
            "Trust_Thresholds", 
            "Value_Statements",
            "Recognition_Loop", 
            "Implementation_Requirements",
            "Golden_Ratio_Relationships"
        ]
        
        # Ensure local storage directory exists
        os.makedirs(self.local_storage_path, exist_ok=True)
        
        # Bach-inspired sampling sequences
        self.fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        
    def process_transcript(self, transcript: Dict[str, Any]) -> ExtractedPatterns:
        """Process a transcript locally, extracting patterns while preserving privacy."""
        # Extract basic metadata
        transcript_id = transcript.get("id", str(uuid.uuid4()))
        timestamp = transcript.get("timestamp", 0)
        text_content = transcript.get("content", "")
        
        # Store the original transcript locally (in production, this would be encrypted)
        self._store_local_transcript(transcript_id, transcript)
        
        # Extract patterns using golden ratio sampling
        patterns = self._extract_patterns(transcript_id, text_content)
        
        # Calculate harmony index
        harmony_index = self._calculate_harmony_index(patterns)
        
        # Create metadata (safe for cloud transmission)
        metadata = TranscriptMetadata(
            transcript_id=transcript_id,
            timestamp=timestamp,
            duration=len(text_content) / 1000,  # Rough estimate
            participant_count=len(set(p.get("speaker", "") for p in transcript.get("participants", []))),
            topic_hash=hashlib.sha256(transcript.get("topic", "").encode()).hexdigest()[:16],
            pattern_count=len(patterns),
            pattern_types={p_type: sum(1 for p in patterns if p.pattern_type == p_type) 
                          for p_type in self.pattern_categories},
            word_count=len(text_content.split()),
            harmony_index=harmony_index
        )
        
        return ExtractedPatterns(
            transcript_metadata=metadata,
            patterns=patterns
        )
    
    def _store_local_transcript(self, transcript_id: str, transcript: Dict[str, Any]) -> None:
        """Store the original transcript locally for future reference."""
        filepath = os.path.join(self.local_storage_path, f"{transcript_id}.json")
        with open(filepath, 'w') as f:
            json.dump(transcript, f, indent=2)
    
    def _extract_patterns(self, transcript_id: str, text: str) -> List[Pattern]:
        """Extract patterns from text using golden ratio sampling."""
        patterns = []
        lines = text.strip().split('\n')
        
        # Golden ratio sampling of lines
        sampled_indices = self._golden_ratio_sample_indices(len(lines))
        
        for i in sampled_indices:
            if i < len(lines):
                line = lines[i]
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Calculate phi position (position in the text normalized to 0-1)
                phi_position = i / len(lines) if len(lines) > 1 else 0.5
                
                # Simple pattern categorization
                # In production, this would use more sophisticated analysis
                pattern_type = self._categorize_pattern(line)
                
                # Create a content hash that doesn't reveal the original text
                content_hash = hashlib.sha256(line.encode()).hexdigest()[:16]
                
                # Calculate confidence based on golden ratio proximity
                # Lines closer to golden ratio positions get higher confidence
                phi_distances = [abs(phi_position - (i / PHI) % 1) for i in range(1, 6)]
                confidence = 1 - min(phi_distances)
                
                # Create pattern object
                pattern = Pattern(
                    pattern_id=f"{transcript_id}_{i}",
                    pattern_type=pattern_type,
                    confidence=confidence,
                    hash=content_hash,
                    phi_position=phi_position,
                    context_size=len(line),
                    metadata={
                        "line_number": i,
                        "word_count": len(line.split()),
                        "local_path": f"{transcript_id}.json"
                    }
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def _golden_ratio_sample_indices(self, length: int) -> List[int]:
        """Sample indices using golden ratio for natural distribution."""
        if length <= 5:
            # For short texts, include everything
            return list(range(length))
        
        # Base sampling using Fibonacci numbers
        indices = [i for i in self.fibonacci if i < length]
        
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
    
    def _categorize_pattern(self, text: str) -> str:
        """Categorize a pattern based on its content."""
        text_lower = text.lower()
        
        # Simple keyword matching for categories
        # In production, this would use more sophisticated analysis
        keywords = {
            "Core_Principles": ["truth", "foundation", "core", "principle", "charter", "trust"],
            "Trust_Thresholds": ["threshold", "boundary", "limit", "trust", "confidence"],
            "Value_Statements": ["value", "worth", "important", "significant", "meaningful"],
            "Recognition_Loop": ["pattern", "recognize", "identify", "notice", "observe"],
            "Implementation_Requirements": ["implement", "require", "need", "must", "should", "develop"],
            "Golden_Ratio_Relationships": ["ratio", "proportion", "harmony", "balance", "phi", "golden"]
        }
        
        # Check each category
        for category, category_keywords in keywords.items():
            if any(keyword in text_lower for keyword in category_keywords):
                return category
        
        # Default category
        return "Uncategorized"
    
    def _calculate_harmony_index(self, patterns: List[Pattern]) -> float:
        """Calculate harmony index based on pattern distribution."""
        if not patterns:
            return 0.0
        
        # Count patterns by type
        type_counts = {}
        for pattern in patterns:
            type_counts[pattern.pattern_type] = type_counts.get(pattern.pattern_type, 0) + 1
        
        # Calculate entropy
        total = sum(type_counts.values())
        probabilities = [count/total for count in type_counts.values()]
        entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probabilities)
        max_entropy = math.log(len(type_counts)) if len(type_counts) > 0 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Calculate golden ratio alignment
        # Ideal distribution follows powers of 1/phi
        counts = sorted(type_counts.values(), reverse=True)
        ideal = [(1/PHI) ** i for i in range(len(counts))]
        
        # Normalize ideal distribution
        ideal_sum = sum(ideal)
        ideal = [i/ideal_sum for i in ideal]
        
        # Normalize actual distribution
        actual = [c/total for c in counts]
        
        # Calculate mean squared error between distributions
        if len(actual) < len(ideal):
            actual.extend([0] * (len(ideal) - len(actual)))
        elif len(ideal) < len(actual):
            ideal.extend([0] * (len(actual) - len(ideal)))
        
        mse = sum((a-i)**2 for a, i in zip(actual, ideal)) / len(ideal)
        
        # Harmony index: balance of entropy and golden ratio alignment
        # Higher entropy (diversity) is good, lower MSE (alignment with golden ratio) is good
        harmony = (1 - normalized_entropy) * (1 - mse)
        
        return max(0, min(1, harmony))
    
    def retrieve_local_transcript(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a locally stored transcript by ID."""
        filepath = os.path.join(self.local_storage_path, f"{transcript_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    def retrieve_context_for_pattern(self, pattern: Pattern) -> Optional[str]:
        """Retrieve the original context for a pattern."""
        # Get the transcript ID from the pattern ID
        transcript_id = pattern.pattern_id.split('_')[0] if '_' in pattern.pattern_id else None
        if not transcript_id:
            return None
        
        # Retrieve the transcript
        transcript = self.retrieve_local_transcript(transcript_id)
        if not transcript:
            return None
        
        # Get the line number from metadata
        line_number = pattern.metadata.get("line_number")
        if line_number is None:
            return None
        
        # Extract the context
        content = transcript.get("content", "")
        lines = content.strip().split('\n')
        
        if line_number < len(lines):
            # Return the line and surrounding context
            start = max(0, line_number - 1)
            end = min(len(lines), line_number + 2)
            return '\n'.join(lines[start:end])
        
        return None

# Create singleton instance
processor = EdgeProcessor()