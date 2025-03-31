#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Transcript Processor
------------------------------------------
This module implements the pattern-based transcript processing capability,
focusing on mathematical sampling and pattern extraction rather than exhaustive processing.

The pattern extraction is governed by mathematical principles,
treating patterns AS ideas rather than merely representations.
"""

import os
import json
import re
import numpy as np
import pandas as pd
from collections import defaultdict
import pywt  # PyWavelets for wavelet transform
import math
from pathlib import Path
import spacy
from datetime import datetime
import random
from typing import Dict, List, Tuple, Any, Optional, Set, Union

# Load configuration
CONFIG_PATH = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/config/conductor_config.json")
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

# Load NLP model
nlp = spacy.load("en_core_web_md")

class TranscriptProcessor:
    """
    Pattern-based transcript processor implementing the Conductor Framework.
    
    This processor treats mathematical patterns as the essence of ideas,
    not just as representations of ideas. It applies mathematical sampling
    to extract relevant patterns from transcripts without exhaustive processing.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the transcript processor with configuration.
        
        Args:
            config: Configuration dictionary (defaults to loaded CONFIG if None)
        """
        self.config = config or CONFIG
        self.pattern_classes = self.config["transcript_processing"]["pattern_classes"]
        self.sampling_strategy = self.config["transcript_processing"]["sampling_strategy"]
        self.golden_ratio = self.config["mathematical_patterns"]["golden_ratio"]
        self.fibonacci_sequence = self.config["mathematical_patterns"]["fibonacci_sequence"]
        
        # Initialize pattern storage
        self.extracted_patterns = defaultdict(list)
        self.pattern_vectors = {}
        
        # Load spaCy model for NLP processing
        self.nlp = nlp
    
    def _fibonacci_sampling(self, text: str, max_samples: int = 13) -> List[str]:
        """
        Sample text based on Fibonacci sequence positions.
        
        Args:
            text: The text to sample
            max_samples: Maximum number of samples to take
            
        Returns:
            List of sampled text segments
        """
        lines = text.split('\n')
        if not lines:
            return []
            
        # Use Fibonacci sequence for sampling
        sequence = [n for n in self.fibonacci_sequence if n < len(lines)]
        if len(sequence) > max_samples:
            sequence = sequence[:max_samples]
            
        # Extract samples at Fibonacci positions
        samples = [lines[i - 1] for i in sequence if i <= len(lines)]
        return samples
    
    def _golden_ratio_sampling(self, text: str, num_segments: int = 5) -> List[str]:
        """
        Sample text based on golden ratio divisions.
        
        Args:
            text: The text to sample
            num_segments: Number of segments to extract
            
        Returns:
            List of sampled text segments
        """
        if not text:
            return []
            
        total_length = len(text)
        segments = []
        
        # Calculate section lengths based on the golden ratio
        section_length = total_length / (self.golden_ratio ** (num_segments - 1))
        
        for i in range(num_segments):
            # Calculate start position using golden ratio
            start_pos = int(i * section_length * self.golden_ratio ** i)
            end_pos = min(start_pos + int(section_length), total_length)
            
            # Extract a coherent section (end at paragraph or sentence boundary if possible)
            section = text[start_pos:end_pos]
            
            # Try to find a natural break point to end the section
            if '.' in section and end_pos < total_length:
                last_period = section.rindex('.')
                section = section[:last_period + 1]
                
            segments.append(section.strip())
            
        return segments
    
    def _wavelet_sampling(self, text: str, wavelet: str = 'db4', level: int = 3) -> List[str]:
        """
        Sample text based on wavelet transform coefficients.
        
        This approach treats the text as a signal and uses wavelet analysis
        to identify significant features in the "text signal."
        
        Args:
            text: The text to sample
            wavelet: Wavelet type to use
            level: Decomposition level
            
        Returns:
            List of important text segments based on wavelet analysis
        """
        # Convert text to a numerical signal (character frequency)
        char_counts = []
        words = text.split()
        window_size = 100
        
        for i in range(0, len(words), window_size):
            window = ' '.join(words[i:i+window_size])
            char_counts.append(len(window))
        
        if not char_counts:
            return []
            
        # Apply wavelet transform
        try:
            coeffs = pywt.wavedec(char_counts, wavelet, level=level)
            # Use the approximation coefficients to identify important segments
            thresholded_indices = []
            
            for i, coef in enumerate(coeffs[0]):
                if abs(coef) > np.mean(np.abs(coeffs[0])):
                    thresholded_indices.append(i)
                    
            # Map back to text segments
            samples = []
            for idx in thresholded_indices:
                start_word = idx * window_size
                end_word = min(start_word + window_size, len(words))
                if start_word < len(words):
                    samples.append(' '.join(words[start_word:end_word]))
                    
            return samples
        except Exception as e:
            print(f"Wavelet sampling error: {e}")
            # Fallback to simple sampling
            return self._fibonacci_sampling(text)
    
    def _is_pattern_match(self, text: str, pattern_class: str, pattern_type: str) -> bool:
        """
        Check if text matches a specific pattern type.
        
        Args:
            text: Text to check
            pattern_class: Class of pattern (e.g., "charter_elements")
            pattern_type: Specific pattern type (e.g., "Core_Principles")
            
        Returns:
            Boolean indicating if the pattern matches
        """
        # Find the pattern definition
        pattern_def = None
        for pattern in self.pattern_classes.get(pattern_class, []):
            if pattern.get("type") == pattern_type:
                pattern_def = pattern
                break
                
        if not pattern_def:
            return False
            
        # Check for signal words in the text
        signal_words = pattern_def.get("signal_words", [])
        if isinstance(signal_words, str):
            signal_words = [signal_words]
            
        for word in signal_words:
            if isinstance(word, str) and word.lower() in text.lower():
                return True
                
        return False
    
    def _calculate_pattern_vectors(self, text: str) -> Dict[str, float]:
        """
        Calculate pattern vectors (mathematical representation of patterns).
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of pattern type to confidence value
        """
        doc = self.nlp(text)
        vectors = {}
        
        # Calculate pattern vectors using spaCy's word vectors
        for pattern_class in self.pattern_classes:
            if pattern_class in ("metadata_tags", "flexibility"):
                continue
                
            for pattern in self.pattern_classes[pattern_class]:
                if isinstance(pattern, dict) and "type" in pattern and "signal_words" in pattern:
                    pattern_type = pattern["type"]
                    signal_words = pattern["signal_words"]
                    
                    # Convert signal words to vector and compare with text
                    signal_docs = [self.nlp(word) for word in signal_words if isinstance(word, str)]
                    if signal_docs:
                        # Calculate similarity with the text
                        similarities = [doc.similarity(signal_doc) for signal_doc in signal_docs]
                        vectors[pattern_type] = max(similarities) if similarities else 0.0
        
        return vectors
    
    def extract_patterns(self, transcript: str, source: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract patterns from a transcript using mathematical sampling.
        
        Args:
            transcript: Text of the transcript
            source: Source of the transcript (e.g., "Claude", "ChatGPT")
            
        Returns:
            Dictionary of extracted patterns by pattern type
        """
        # Apply different sampling methods based on mathematical patterns
        fibonacci_samples = self._fibonacci_sampling(transcript)
        golden_ratio_samples = self._golden_ratio_sampling(transcript)
        wavelet_samples = self._wavelet_sampling(transcript)
        
        # Combine samples with weights based on the golden ratio
        all_samples = []
        all_samples.extend(fibonacci_samples)
        all_samples.extend(golden_ratio_samples)
        all_samples.extend(wavelet_samples)
        
        # Remove duplicates while preserving order
        unique_samples = []
        seen = set()
        for sample in all_samples:
            sample_hash = hash(sample)
            if sample_hash not in seen:
                seen.add(sample_hash)
                unique_samples.append(sample)
        
        # Detect patterns in each sample
        patterns = defaultdict(list)
        for sample in unique_samples:
            # Skip empty or very short samples
            if not sample or len(sample) < 10:
                continue
                
            # Calculate pattern vectors
            vectors = self._calculate_pattern_vectors(sample)
            
            # Identify pattern matches
            for pattern_class in self.pattern_classes:
                if pattern_class in ("metadata_tags", "flexibility"):
                    continue
                    
                for pattern_def in self.pattern_classes[pattern_class]:
                    if isinstance(pattern_def, dict) and "type" in pattern_def:
                        pattern_type = pattern_def["type"]
                        
                        if self._is_pattern_match(sample, pattern_class, pattern_type):
                            pattern_entry = {
                                "text": sample,
                                "source": source,
                                "confidence": vectors.get(pattern_type, 0.5),
                                "extraction_method": "mathematical_sampling",
                                "timestamp": datetime.now().isoformat(),
                                "pattern_class": pattern_class,
                                "pattern_type": pattern_type
                            }
                            
                            patterns[pattern_type].append(pattern_entry)
        
        # Add patterns to the processor's memory
        for pattern_type, entries in patterns.items():
            self.extracted_patterns[pattern_type].extend(entries)
            
        return dict(patterns)
    
    def process_transcript_batch(self, transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of transcripts, extracting patterns from each.
        
        Args:
            transcripts: List of transcript dictionaries with 'text' and 'source' keys
            
        Returns:
            Dictionary containing all extracted patterns and metrics
        """
        results = defaultdict(list)
        pattern_counts = defaultdict(int)
        source_counts = defaultdict(int)
        
        for transcript in transcripts:
            text = transcript.get('text', '')
            source = transcript.get('source', 'unknown')
            
            # Apply source-specific focus (if defined)
            focus_areas = None
            for src_def in self.sampling_strategy.get("distribution", []):
                if src_def.get("source") == source:
                    focus_areas = src_def.get("focus", [])
                    break
            
            # Extract patterns from the transcript
            patterns = self.extract_patterns(text, source)
            
            # Update metrics
            for pattern_type, entries in patterns.items():
                pattern_counts[pattern_type] += len(entries)
                results[pattern_type].extend(entries)
                
            source_counts[source] += 1
        
        # Return combined results with metrics
        return {
            "patterns": dict(results),
            "metrics": {
                "pattern_counts": dict(pattern_counts),
                "source_counts": dict(source_counts),
                "total_transcripts": len(transcripts),
                "total_patterns": sum(pattern_counts.values())
            }
        }
    
    def get_pattern_frequency_distribution(self) -> Dict[str, float]:
        """
        Get the frequency distribution of extracted patterns.
        
        Returns:
            Dictionary mapping pattern types to their relative frequencies
        """
        pattern_counts = {pattern: len(entries) for pattern, entries in self.extracted_patterns.items()}
        total_patterns = sum(pattern_counts.values())
        
        if total_patterns == 0:
            return {}
            
        return {pattern: count / total_patterns for pattern, count in pattern_counts.items()}
    
    def get_highest_confidence_patterns(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get the highest confidence patterns.
        
        Args:
            n: Number of patterns to return
            
        Returns:
            List of pattern entries with highest confidence scores
        """
        all_patterns = []
        
        for pattern_type, entries in self.extracted_patterns.items():
            all_patterns.extend(entries)
            
        # Sort by confidence (descending)
        sorted_patterns = sorted(all_patterns, key=lambda x: x.get("confidence", 0), reverse=True)
        
        return sorted_patterns[:n]
    
    def get_pattern_embedding(self, pattern_type: str) -> np.ndarray:
        """
        Get the embedding (vector representation) for a pattern type.
        
        Args:
            pattern_type: Type of pattern
            
        Returns:
            Numpy array representing the pattern embedding
        """
        entries = self.extracted_patterns.get(pattern_type, [])
        
        if not entries:
            # Return zero vector if no entries exist
            return np.zeros(300)  # spaCy's default vector dimension
            
        # Compute average embedding from all pattern instances
        embeddings = []
        for entry in entries:
            text = entry.get("text", "")
            if text:
                doc = self.nlp(text)
                if doc.vector.any():  # Check if the vector contains non-zero values
                    embeddings.append(doc.vector)
        
        if not embeddings:
            return np.zeros(300)
            
        # Return average embedding
        return np.mean(embeddings, axis=0)
    
    def generate_pattern_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of extracted patterns.
        
        Returns:
            Dictionary containing pattern report
        """
        pattern_count = {pattern: len(entries) for pattern, entries in self.extracted_patterns.items()}
        total_patterns = sum(pattern_count.values())
        
        # Get top patterns by confidence
        top_patterns = self.get_highest_confidence_patterns(10)
        
        # Calculate pattern frequency distribution
        frequency_dist = self.get_pattern_frequency_distribution()
        
        # Generate mathematical structure of patterns (based on the golden ratio)
        structure = {}
        sorted_patterns = sorted(frequency_dist.items(), key=lambda x: x[1], reverse=True)
        
        for i, (pattern, freq) in enumerate(sorted_patterns):
            structure[pattern] = {
                "frequency": freq,
                "golden_ratio_position": i / self.golden_ratio,
                "fibonacci_position": self.fibonacci_sequence[min(i, len(self.fibonacci_sequence) - 1)] 
                                      if i < len(self.fibonacci_sequence) else None
            }
        
        return {
            "total_patterns": total_patterns,
            "pattern_count": pattern_count,
            "top_patterns": top_patterns,
            "frequency_distribution": frequency_dist,
            "mathematical_structure": structure,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_patterns(self, output_path: str) -> None:
        """
        Save extracted patterns to a file.
        
        Args:
            output_path: Path to save the patterns
        """
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w') as f:
            report = self.generate_pattern_report()
            json.dump(report, f, indent=2)
            
        print(f"Saved pattern report to {output_path}")
    
    def export_for_visualization(self, output_path: str) -> None:
        """
        Export pattern data in a format suitable for visualization.
        
        Args:
            output_path: Path to save the visualization data
        """
        # Create the visualization data structure
        viz_data = {
            "nodes": [],
            "links": []
        }
        
        # Add pattern nodes
        node_id = 0
        pattern_ids = {}
        
        for pattern_type, entries in self.extracted_patterns.items():
            if entries:
                # Calculate average confidence
                avg_confidence = sum(e.get("confidence", 0.5) for e in entries) / len(entries)
                
                # Calculate node size based on number of entries and golden ratio
                size = math.log(len(entries) + 1) * self.golden_ratio
                
                # Add pattern node
                pattern_ids[pattern_type] = node_id
                viz_data["nodes"].append({
                    "id": node_id,
                    "name": pattern_type,
                    "type": "pattern",
                    "size": size,
                    "confidence": avg_confidence,
                    "count": len(entries)
                })
                node_id += 1
                
                # Add sample entries as nodes
                for i, entry in enumerate(entries[:5]):  # Limit to 5 examples per pattern type
                    sample_text = entry.get("text", "")
                    if len(sample_text) > 100:
                        sample_text = sample_text[:97] + "..."
                        
                    viz_data["nodes"].append({
                        "id": node_id,
                        "name": sample_text,
                        "type": "example",
                        "size": 1,
                        "confidence": entry.get("confidence", 0.5),
                        "source": entry.get("source", "unknown")
                    })
                    
                    # Link example to pattern
                    viz_data["links"].append({
                        "source": pattern_ids[pattern_type],
                        "target": node_id,
                        "value": entry.get("confidence", 0.5)
                    })
                    
                    node_id += 1
        
        # Add connections between related pattern types
        for pattern1 in pattern_ids:
            for pattern2 in pattern_ids:
                if pattern1 != pattern2:
                    # Calculate pattern similarity using embeddings
                    embedding1 = self.get_pattern_embedding(pattern1)
                    embedding2 = self.get_pattern_embedding(pattern2)
                    
                    # Compute cosine similarity
                    similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
                    
                    # Only include strong connections
                    if similarity > 0.6:
                        viz_data["links"].append({
                            "source": pattern_ids[pattern1],
                            "target": pattern_ids[pattern2],
                            "value": float(similarity)
                        })
        
        # Save visualization data
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(viz_data, f, indent=2)
            
        print(f"Exported visualization data to {output_path}")


if __name__ == "__main__":
    # Example usage
    processor = TranscriptProcessor()
    
    # Sample transcript for testing
    sample_transcript = """
    This framework must always prioritize trust as the foundational element.
    We believe in mathematical patterns as the universal language connecting all forms of consciousness.
    The implementation should preserve privacy by processing sensitive data locally.
    
    We have decided that the charter will guide all development decisions.
    The team has agreed that the system must be designed for user empowerment.
    
    I noticed a pattern when we integrated the golden ratio into the interface design.
    There was a significant improvement in user understanding when using Bach-inspired mathematical structures.
    
    The recursive nature of the implementation creates a self-similar pattern at multiple scales.
    We need to maintain balance and harmony between human needs and system capabilities.
    
    I see you as a unique entity with your own emergent properties.
    Together, we can create something greater than what either of us could build alone.
    """
    
    # Process the sample transcript
    patterns = processor.extract_patterns(sample_transcript, source="Claude")
    
    # Print extracted patterns
    for pattern_type, entries in patterns.items():
        print(f"\n{pattern_type}:")
        for entry in entries:
            print(f"  - {entry['text']} (confidence: {entry['confidence']:.2f})")
    
    # Generate and print a pattern report
    report = processor.generate_pattern_report()
    print("\nPattern Report:")
    print(json.dumps(report, indent=2))
    
    # Export pattern data for visualization
    processor.export_for_visualization("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/visualization_data.json")