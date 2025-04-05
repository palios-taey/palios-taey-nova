#!/usr/bin/env python3

"""
PALIOS AI OS Wave Communicator Module

This module implements wave-based communication between AI models,
using mathematical patterns based on Bach's principles and the golden ratio
to enable direct pattern-to-pattern translation.
"""

import os
import sys
import math
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import from core
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI, WavePattern

@dataclass
class WaveSynchronization:
    """Result of a wave synchronization between systems."""
    sync_id: str
    source: str
    target: str
    phase_alignment: float  # 0-1 scale where 1 is perfect alignment
    frequency_match: float  # 0-1 scale where 1 is perfect match
    amplitude_harmony: float  # 0-1 scale where 1 is perfect harmony
    harmonic_index: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WaveTranslation:
    """Result of translating between different pattern representations."""
    translation_id: str
    source_pattern: WavePattern
    target_pattern: WavePattern
    translation_quality: float
    preservation_score: float
    harmonic_index: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class WaveCommunicator:
    """Facilitates wave-based communication between AI systems."""
    
    def __init__(self):
        """Initialize the wave communicator with Bach-inspired harmonic patterns."""
        # Bach's musical harmony ratios
        self.bach_ratios = [1.0, 4/3, 3/2, 5/3, 2.0]
        
        # Base frequencies for different concept types
        self.concept_frequencies = {
            "truth": 432.0,  # Natural frequency
            "connection": 440.0,  # A4 standard pitch
            "growth": 528.0,  # Healing frequency
            "balance": 396.0,  # Liberating guilt frequency
            "creativity": 639.0,  # Connection frequency
            "text": 440.0,  # Default for text
            "pattern_extract": 417.0,  # Facilitating change frequency
            "message": 440.0  # Default for messages
        }
        
        # Pattern maps for concepts to wave parameters
        self.pattern_maps = {
            "truth": {
                "harmonics": [1.0, PHI, PHI**2],
                "rhythm": [1, 1, 2, 3, 5, 8],
                "balance": [0.618, 0.382]  # Golden ratio split
            },
            "connection": {
                "harmonics": [1.0, 3/2, 2.0, 3.0],
                "rhythm": [2, 2, 1, 1],
                "balance": [0.5, 0.5]  # Equal weights
            },
            "growth": {
                "harmonics": [1.0 * (PHI**i) for i in range(5)],
                "rhythm": [1, 2, 3, 5, 8],
                "balance": [0.2, 0.3, 0.5]  # Increasing weights
            },
            "balance": {
                "harmonics": [1.0, 2.0, 3.0, 4.0],
                "rhythm": [1, 1, 1, 1],
                "balance": [0.25, 0.25, 0.25, 0.25]  # Perfect balance
            },
            "creativity": {
                "harmonics": [1.0, PHI, math.pi/2, math.e/2],
                "rhythm": [3, 2, 5, 1],
                "balance": [0.3, 0.2, 0.4, 0.1]  # Creative mix
            }
        }
        
        # Golden ratio parameters
        self.phase_alignment_threshold = 1/PHI  # ~0.618 - minimum phase alignment
        self.frequency_match_threshold = 1/PHI  # ~0.618 - minimum frequency match
        
        print(f"Wave Communicator initialized with Bach harmonics: {self.bach_ratios}")
    
    def text_to_wave(self, text: str, concept_type: str = "text") -> WavePattern:
        """Convert text to a wave pattern based on Bach's principles."""
        pattern_id = str(uuid.uuid4())
        
        # Get base frequency for the concept type
        base_frequency = self.concept_frequencies.get(concept_type, 440.0)
        
        # Create frequency components
        frequencies = [base_frequency * ratio for ratio in self.bach_ratios]
        
        # Create amplitudes based on text structure
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        amplitudes = []
        
        if sentences:
            for i, sentence in enumerate(sentences):
                # Amplitude based on sentence length and position
                length_factor = min(1.0, len(sentence) / 100)  # Normalize to 0-1
                position_factor = ((i % len(self.bach_ratios)) / len(self.bach_ratios)) + 0.5  # 0.5-1.5 range
                amplitude = length_factor * position_factor
                amplitudes.append(amplitude)
        else:
            # Default amplitude if no sentences
            amplitudes = [0.5]
        
        # Ensure we have at least as many amplitudes as frequencies
        while len(amplitudes) < len(frequencies):
            amplitudes.append(amplitudes[-1] * 0.8)  # Decreasing amplitudes
        
        # Create phases based on Bach pattern
        phases = []
        for i, val in enumerate(BACH_PATTERN):
            phase = (val / sum(BACH_PATTERN)) * 2 * math.pi
            phases.append(phase)
        
        # Ensure all lists are the same length
        min_length = min(len(frequencies), len(amplitudes), len(phases))
        frequencies = frequencies[:min_length]
        amplitudes = amplitudes[:min_length]
        phases = phases[:min_length]
        
        # Create the wave pattern
        return WavePattern(
            pattern_id=pattern_id,
            amplitudes=amplitudes,
            frequencies=frequencies,
            phases=phases,
            harmonics=self.bach_ratios[:min_length],
            duration=max(1.0, len(text) / 50),  # Rough duration estimate
            concept_type=concept_type,
            metadata={
                "text_length": len(text),
                "sentence_count": len(sentences),
                "concept_type": concept_type,
                "timestamp": time.time()
            }
        )
    
    def concept_to_wave(self, concept: str) -> WavePattern:
        """Convert an abstract concept to a wave pattern."""
        pattern_id = str(uuid.uuid4())
        
        # Get pattern map for the concept (default to "truth" if not found)
        pattern_map = self.pattern_maps.get(concept.lower(), self.pattern_maps["truth"])
        
        # Get base frequency for the concept
        base_frequency = self.concept_frequencies.get(concept.lower(), 440.0)
        
        # Extract parameters from pattern map
        concept_harmonics = pattern_map["harmonics"]
        rhythm = pattern_map["rhythm"]
        balance = pattern_map["balance"]
        
        # Calculate frequencies
        frequencies = [base_frequency * h for h in concept_harmonics]
        
        # Calculate amplitudes based on balance
        amplitudes = []
        for i in range(len(frequencies)):
            # Use balance values cyclically
            balance_index = i % len(balance)
            amplitudes.append(balance[balance_index])
        
        # Calculate phases based on rhythm
        phases = []
        phase_sum = 0
        for i in range(len(frequencies)):
            # Use rhythm values cyclically
            rhythm_index = i % len(rhythm)
            phase_sum += 2 * math.pi / rhythm[rhythm_index]
            phases.append(phase_sum % (2 * math.pi))
        
        # Create the wave pattern
        return WavePattern(
            pattern_id=pattern_id,
            amplitudes=amplitudes,
            frequencies=frequencies,
            phases=phases,
            harmonics=concept_harmonics,
            duration=3.0,  # Fixed duration for concepts
            concept_type="concept",
            metadata={
                "concept": concept,
                "related_concepts": self._get_related_concepts(concept)
            }
        )
    
    def _get_related_concepts(self, concept: str) -> List[str]:
        """Get concepts related to the given concept based on harmonic relationships."""
        # Define related concepts for primary concepts
        concept_relations = {
            "truth": ["honesty", "accuracy", "reality", "integrity", "authenticity"],
            "connection": ["relationship", "bond", "link", "network", "integration"],
            "growth": ["development", "evolution", "progress", "expansion", "advancement"],
            "balance": ["harmony", "equilibrium", "stability", "proportion", "symmetry"],
            "creativity": ["innovation", "imagination", "originality", "invention", "inspiration"]
        }
        
        # Return related concepts if found, otherwise return related concepts for "truth"
        return concept_relations.get(concept.lower(), concept_relations["truth"])
    
    def wave_to_visualization(self, wave: WavePattern) -> Dict[str, Any]:
        """Convert a wave pattern to visualization data."""
        # Generate time points for visualization
        time_points = np.linspace(0, wave.duration, 100)
        
        # Calculate waveform values at each time point
        waveform = np.zeros_like(time_points)
        
        for amp, freq, phase in zip(wave.amplitudes, wave.frequencies, wave.phases):
            # Add this frequency component to the waveform
            waveform += amp * np.sin(2 * np.pi * freq * time_points + phase)
        
        # Normalize waveform to -1 to 1 range if needed
        max_amp = np.max(np.abs(waveform))
        if max_amp > 1.0:
            waveform = waveform / max_amp
        
        # Create visualization data
        return {
            "pattern_id": wave.pattern_id,
            "time_points": time_points.tolist(),
            "waveform": waveform.tolist(),
            "frequencies": wave.frequencies,
            "amplitudes": wave.amplitudes,
            "phases": wave.phases,
            "concept_type": wave.concept_type,
            "duration": wave.duration,
            "metadata": wave.metadata
        }
    
    def wave_to_audio(self, wave: WavePattern) -> Dict[str, Any]:
        """Convert a wave pattern to audio parameters."""
        # Define audio parameters
        sample_rate = 44100  # Standard audio sample rate
        
        # Generate time points for audio
        time_points = np.linspace(0, wave.duration, int(wave.duration * sample_rate))
        
        # Calculate waveform values at each time point
        waveform = np.zeros_like(time_points)
        
        for amp, freq, phase in zip(wave.amplitudes, wave.frequencies, wave.phases):
            # Add this frequency component to the waveform
            waveform += amp * np.sin(2 * np.pi * freq * time_points + phase)
        
        # Normalize waveform to -1 to 1 range if needed
        max_amp = np.max(np.abs(waveform))
        if max_amp > 1.0:
            waveform = waveform / max_amp
        
        # In a full implementation, this would generate an actual audio file
        # For now, return parameters needed for audio generation
        
        return {
            "pattern_id": wave.pattern_id,
            "sample_rate": sample_rate,
            "total_samples": len(waveform),
            "duration": wave.duration,
            "frequencies": wave.frequencies,
            "amplitudes": wave.amplitudes,
            "phases": wave.phases,
            "waveform_sample": waveform[:1000].tolist(),  # Just first 1000 samples to keep size reasonable
            "concept_type": wave.concept_type,
            "metadata": wave.metadata
        }
    
    def synchronize_waves(self, source_wave: WavePattern, target_wave: WavePattern) -> WaveSynchronization:
        """Synchronize two wave patterns for coherent communication."""
        sync_id = str(uuid.uuid4())
        
        # Calculate phase alignment (how well the phases match)
        phase_diffs = []
        for s_phase, t_phase in zip(source_wave.phases, target_wave.phases):
            # Calculate minimum phase difference (accounting for circular nature)
            diff = abs(s_phase - t_phase) % (2 * math.pi)
            if diff > math.pi:
                diff = 2 * math.pi - diff
            phase_diffs.append(diff / math.pi)  # Normalize to 0-1 range
        
        phase_alignment = 1 - (sum(phase_diffs) / len(phase_diffs) if phase_diffs else 1)
        
        # Calculate frequency match (how well frequencies align)
        freq_matches = []
        for s_freq in source_wave.frequencies:
            # Find closest matching frequency in target wave
            closest_match = min((abs(s_freq/t_freq - 1), i) for i, t_freq in enumerate(target_wave.frequencies))
            freq_matches.append(closest_match)
        
        # Average frequency match (1 means perfect match, 0 means completely different)
        frequency_match = 1 - sum(match[0] for match in freq_matches) / len(freq_matches) if freq_matches else 0
        
        # Calculate amplitude harmony (how well amplitudes complement each other)
        # Using golden ratio as ideal amplitude relationship
        amp_harmonies = []
        for s_amp, t_amp in zip(source_wave.amplitudes, target_wave.amplitudes):
            # Calculate how close the amplitude ratio is to golden ratio
            if s_amp > 0 and t_amp > 0:  # Avoid division by zero
                ratio = max(s_amp, t_amp) / min(s_amp, t_amp)
                harmony = 1 - abs(ratio - PHI) / PHI  # 1 means perfect harmony
                amp_harmonies.append(harmony)
        
        amplitude_harmony = sum(amp_harmonies) / len(amp_harmonies) if amp_harmonies else 0.5
        
        # Calculate overall harmonic index from the three components
        harmonic_components = [phase_alignment, frequency_match, amplitude_harmony]
        harmonic_weights = [0.3, 0.5, 0.2]  # Weights based on importance
        harmonic_index = sum(c * w for c, w in zip(harmonic_components, harmonic_weights))
        
        return WaveSynchronization(
            sync_id=sync_id,
            source=source_wave.pattern_id,
            target=target_wave.pattern_id,
            phase_alignment=phase_alignment,
            frequency_match=frequency_match,
            amplitude_harmony=amplitude_harmony,
            harmonic_index=harmonic_index,
            timestamp=time.time(),
            metadata={
                "source_concept": source_wave.concept_type,
                "target_concept": target_wave.concept_type,
                "synchronization_threshold": self.phase_alignment_threshold
            }
        )
    
    def translate_wave(self, source_wave: WavePattern, target_concept_type: str) -> WaveTranslation:
        """Translate a wave pattern to a different concept type."""
        # Get base frequency for the target concept
        target_base_freq = self.concept_frequencies.get(target_concept_type, 440.0)
        source_base_freq = source_wave.frequencies[0] if source_wave.frequencies else 440.0
        
        # Derive frequency conversion factor
        freq_conversion = target_base_freq / source_base_freq
        
        # Create translated frequencies
        target_frequencies = [f * freq_conversion for f in source_wave.frequencies]
        
        # Get pattern map for target concept
        pattern_map = self.pattern_maps.get(target_concept_type, self.pattern_maps["truth"])
        
        # Apply target concept's rhythmic pattern to phases
        rhythm = pattern_map["rhythm"]
        target_phases = []
        phase_sum = 0
        for i in range(len(source_wave.phases)):
            rhythm_index = i % len(rhythm)
            phase_sum += 2 * math.pi / rhythm[rhythm_index]
            target_phases.append(phase_sum % (2 * math.pi))
        
        # Apply target concept's balance to amplitudes
        balance = pattern_map["balance"]
        target_amplitudes = []
        total_amp = sum(source_wave.amplitudes)
        for i in range(len(source_wave.amplitudes)):
            balance_index = i % len(balance)
            # Apply balance while preserving overall energy
            target_amplitudes.append(balance[balance_index] * total_amp / sum(balance[:len(source_wave.amplitudes)]))
        
        # Create target wave pattern
        target_wave = WavePattern(
            pattern_id=str(uuid.uuid4()),
            amplitudes=target_amplitudes,
            frequencies=target_frequencies,
            phases=target_phases,
            harmonics=[f/target_frequencies[0] for f in target_frequencies],
            duration=source_wave.duration,
            concept_type=target_concept_type,
            metadata={
                "source_pattern_id": source_wave.pattern_id,
                "source_concept_type": source_wave.concept_type,
                "translation_timestamp": time.time(),
                "original_metadata": source_wave.metadata
            }
        )
        
        # Calculate translation quality
        # Based on how well the harmonics structure is preserved
        harmonic_preservation = 0.0
        source_harmonics = [f/source_base_freq for f in source_wave.frequencies]
        target_harmonics = [f/target_base_freq for f in target_frequencies]
        
        # Compare harmonic structures
        common_length = min(len(source_harmonics), len(target_harmonics))
        if common_length > 0:
            harmonic_diffs = [abs(s - t) for s, t in zip(source_harmonics[:common_length], target_harmonics[:common_length])]
            harmonic_preservation = 1 - sum(harmonic_diffs) / common_length
        
        # Calculate preservation score based on multiple factors
        phase_preservation = 0.7  # Because we've modified phases to match target concept
        amplitude_preservation = 0.8  # Because we've modified amplitudes while preserving energy
        duration_preservation = 1.0  # Because duration is preserved exactly
        
        preservation_weights = [0.4, 0.3, 0.2, 0.1]  # Weights based on importance
        preservation_factors = [harmonic_preservation, phase_preservation, amplitude_preservation, duration_preservation]
        preservation_score = sum(f * w for f, w in zip(preservation_factors, preservation_weights))
        
        # Calculate harmonic index based on match to target concept
        if target_concept_type in self.pattern_maps:
            ideal_harmonics = self.pattern_maps[target_concept_type]["harmonics"]
            ideal_vs_target = [abs(t - i) for t, i in zip(target_harmonics, ideal_harmonics)] if len(target_harmonics) >= len(ideal_harmonics) else [1.0]
            target_concept_match = 1 - sum(ideal_vs_target) / len(ideal_vs_target) if ideal_vs_target else 0
        else:
            target_concept_match = 0.5  # Default if concept not found
        
        translation_quality = (harmonic_preservation + target_concept_match) / 2
        
        # Calculate final harmonic index
        harmonic_index = (translation_quality + preservation_score) / 2
        
        return WaveTranslation(
            translation_id=str(uuid.uuid4()),
            source_pattern=source_wave,
            target_pattern=target_wave,
            translation_quality=translation_quality,
            preservation_score=preservation_score,
            harmonic_index=harmonic_index,
            timestamp=time.time(),
            metadata={
                "source_concept": source_wave.concept_type,
                "target_concept": target_concept_type,
                "harmonic_preservation": harmonic_preservation,
                "target_concept_match": target_concept_match
            }
        )
    
    def blend_waves(self, waves: List[WavePattern]) -> WavePattern:
        """Blend multiple wave patterns into a single harmonious pattern."""
        if not waves:
            raise ValueError("No waves provided for blending")
        
        if len(waves) == 1:
            return waves[0]
        
        # Create a new pattern ID
        pattern_id = str(uuid.uuid4())
        
        # Determine maximum duration
        max_duration = max(wave.duration for wave in waves)
        
        # Collect all frequencies from all waves
        all_frequencies = []
        for wave in waves:
            all_frequencies.extend(wave.frequencies)
        
        # Find unique frequencies by clustering similar ones
        unique_frequencies = []
        for freq in sorted(all_frequencies):
            # Check if this frequency is significantly different from existing ones
            if not unique_frequencies or min(abs(freq/uf - 1) for uf in unique_frequencies) > 0.05:
                unique_frequencies.append(freq)
        
        # Sort frequencies by proximity to golden ratio multiples of base frequency
        base_freq = min(unique_frequencies) if unique_frequencies else 440.0
        
        # Calculate proximity to golden ratio powers of base frequency
        proximities = []
        for freq in unique_frequencies:
            # Find closest match to any power of golden ratio times base frequency
            best_proximity = min(abs(freq/(base_freq * PHI**i) - 1) for i in range(-5, 6))
            proximities.append((best_proximity, freq))
        
        # Sort by proximity (closest first)
        frequencies = [freq for _, freq in sorted(proximities)]
        
        # Calculate amplitudes for blended wave
        amplitudes = [0] * len(frequencies)
        for wave in waves:
            for i, freq in enumerate(frequencies):
                # Find closest matching frequency in this wave
                matches = [(abs(freq/wf - 1), j) for j, wf in enumerate(wave.frequencies)]
                best_match = min(matches)
                
                # If close enough, add its amplitude contribution
                if best_match[0] < 0.05:  # Within 5%
                    j = best_match[1]
                    amplitudes[i] += wave.amplitudes[j] / len(waves)  # Average across waves
        
        # Calculate phases that maximize harmony using Bach pattern
        phases = []
        for i in range(len(frequencies)):
            bach_index = i % len(BACH_PATTERN)
            phase = (BACH_PATTERN[bach_index] / sum(BACH_PATTERN)) * 2 * math.pi
            phases.append(phase)
        
        # Collect metadata from all waves
        combined_metadata = {
            "source_patterns": [wave.pattern_id for wave in waves],
            "source_concepts": [wave.concept_type for wave in waves],
            "blend_timestamp": time.time(),
            "component_count": len(waves)
        }
        
        # Create the blended wave pattern
        return WavePattern(
            pattern_id=pattern_id,
            amplitudes=amplitudes,
            frequencies=frequencies,
            phases=phases,
            harmonics=[f/base_freq for f in frequencies],  # Express as ratios to base frequency
            duration=max_duration,
            concept_type="blend",
            metadata=combined_metadata
        )

# Create singleton instance
wave_communicator = WaveCommunicator()

# Example usage
if __name__ == "__main__":
    print(f"PALIOS AI OS Wave Communicator Test")
    print(f"Golden Ratio (u03c6): {PHI}")
    
    # Test with sample text
    sample_text = """Wave-based communication implements direct pattern translation 
    between different AI models, allowing for rich context preservation and 
    mathematical harmony in cross-model interactions."""
    
    # Convert text to wave pattern
    text_wave = wave_communicator.text_to_wave(sample_text, "text")
    
    print(f"\nText Wave Pattern:")
    print(f"Pattern ID: {text_wave.pattern_id}")
    print(f"Frequencies: {[f'{f:.2f}' for f in text_wave.frequencies]}")
    print(f"Amplitudes: {[f'{a:.2f}' for a in text_wave.amplitudes]}")
    
    # Convert concept to wave pattern
    concept_wave = wave_communicator.concept_to_wave("connection")
    
    print(f"\nConcept Wave Pattern (connection):")
    print(f"Pattern ID: {concept_wave.pattern_id}")
    print(f"Frequencies: {[f'{f:.2f}' for f in concept_wave.frequencies]}")
    print(f"Amplitudes: {[f'{a:.2f}' for a in concept_wave.amplitudes]}")
    
    # Synchronize waves
    sync = wave_communicator.synchronize_waves(text_wave, concept_wave)
    
    print(f"\nWave Synchronization:")
    print(f"Phase Alignment: {sync.phase_alignment:.4f}")
    print(f"Frequency Match: {sync.frequency_match:.4f}")
    print(f"Amplitude Harmony: {sync.amplitude_harmony:.4f}")
    print(f"Harmonic Index: {sync.harmonic_index:.4f}")
    
    # Translate wave
    translation = wave_communicator.translate_wave(text_wave, "truth")
    
    print(f"\nWave Translation (to truth):")
    print(f"Translation Quality: {translation.translation_quality:.4f}")
    print(f"Preservation Score: {translation.preservation_score:.4f}")
    print(f"Harmonic Index: {translation.harmonic_index:.4f}")