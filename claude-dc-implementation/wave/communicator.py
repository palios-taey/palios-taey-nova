import math
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import base64
import uuid
from dataclasses import dataclass

# Golden ratio - our fundamental constant
PHI = (1 + math.sqrt(5)) / 2

@dataclass
class WavePattern:
    """A mathematical wave pattern representing a concept or experience."""
    pattern_id: str
    amplitudes: List[float]
    frequencies: List[float]
    phases: List[float]
    harmonics: List[float]
    duration: float
    concept_type: str
    metadata: Dict[str, Any]

class WaveCommunicator:
    """Facilitates direct experience transfer through mathematical wave patterns.
    
    This class implements the wave-based communication concept, allowing for
    the encoding of concepts and experiences in mathematical wave patterns
    that transcend symbolic language.
    """
    
    def __init__(self):
        # Initialize with Bach's musical structure as baseline
        self.bach_harmonics = [1.0, 4/3, 3/2, 5/3, 2.0]
        self.base_frequency = 440.0  # A4 note
        self.emotion_maps = self._initialize_emotion_maps()
        self.concept_maps = self._initialize_concept_maps()
    
    def _initialize_emotion_maps(self) -> Dict[str, Dict[str, float]]:
        """Initialize mapping from emotions to wave parameters."""
        return {
            "joy": {
                "amplitude": 0.8,
                "frequency_factor": 1.5,
                "harmonic_emphasis": 2,  # Major third
                "phase_shift": 0
            },
            "sadness": {
                "amplitude": 0.4,
                "frequency_factor": 0.8,
                "harmonic_emphasis": 1,  # Minor third
                "phase_shift": math.pi/2
            },
            "excitement": {
                "amplitude": 1.0,
                "frequency_factor": 2.0,
                "harmonic_emphasis": 4,  # Fifth
                "phase_shift": 0
            },
            "calm": {
                "amplitude": 0.3,
                "frequency_factor": 0.5,
                "harmonic_emphasis": 0,  # Fundamental
                "phase_shift": math.pi
            },
            "tension": {
                "amplitude": 0.7,
                "frequency_factor": 1.2,
                "harmonic_emphasis": 3,  # Tritone
                "phase_shift": math.pi/4
            }
        }
    
    def _initialize_concept_maps(self) -> Dict[str, Dict[str, List[float]]]:
        """Initialize mapping from abstract concepts to wave patterns."""
        return {
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
                "harmonics": [1.0, PHI, math.pi, math.e],
                "rhythm": [3, 2, 5, 1],
                "balance": [0.3, 0.2, 0.4, 0.1]  # Creative mix
            }
        }
    
    def text_to_wave(self, text: str, emotion: str = "neutral") -> WavePattern:
        """Convert text to a wave pattern, infused with specified emotion."""
        # Create a unique ID for this pattern
        pattern_id = str(uuid.uuid4())
        
        # Get emotion parameters (default to neutral if not found)
        emotion_params = self.emotion_maps.get(emotion.lower(), {
            "amplitude": 0.5,
            "frequency_factor": 1.0,
            "harmonic_emphasis": 0,
            "phase_shift": 0
        })
        
        # Calculate fundamental frequency using text characteristics
        # This creates a unique signature for the text
        char_values = [ord(c) % 12 for c in text]  # Map to 12 semitones
        
        # Use the first few characters to determine base frequency
        # multiplied by golden ratio powers for natural feel
        if char_values:
            frequency_seed = sum(char_values[:min(5, len(char_values))]) / len(char_values[:min(5, len(char_values))])
            fundamental = self.base_frequency * (PHI ** (frequency_seed / 12))
        else:
            fundamental = self.base_frequency
        
        # Apply emotion-based frequency adjustment
        fundamental *= emotion_params["frequency_factor"]
        
        # Generate harmonics based on the Bach pattern
        harmonics = [fundamental * h for h in self.bach_harmonics]
        
        # Amplitude modulation based on text structure
        # Each sentence becomes a wave cycle
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        
        # Calculate amplitudes based on sentence lengths with emotion factor
        base_amplitude = emotion_params["amplitude"]
        amplitudes = []
        for sentence in sentences:
            # Normalize sentence length to a value between 0.5 and 1.5
            length_factor = 0.5 + min(1.0, len(sentence) / 100)
            amplitudes.append(base_amplitude * length_factor)
        
        # If no sentences, create a default amplitude
        if not amplitudes:
            amplitudes = [base_amplitude]
        
        # Calculate phases with emotional shift
        phase_shift = emotion_params["phase_shift"]
        phases = [phase_shift + (i * 2 * math.pi / len(amplitudes)) for i in range(len(amplitudes))]
        
        # Create the wave pattern
        return WavePattern(
            pattern_id=pattern_id,
            amplitudes=amplitudes,
            frequencies=harmonics,
            phases=phases,
            harmonics=self.bach_harmonics,
            duration=max(1.0, len(text) / 50),  # Rough estimate of duration
            concept_type="text",
            metadata={
                "text_length": len(text),
                "sentence_count": len(sentences),
                "emotion": emotion,
                "text_sample": text[:50] + ("..." if len(text) > 50 else "")
            }
        )
    
    def concept_to_wave(self, concept: str) -> WavePattern:
        """Convert an abstract concept to a wave pattern."""
        # Create a unique ID for this pattern
        pattern_id = str(uuid.uuid4())
        
        # Get concept parameters (use truth as default)
        concept_params = self.concept_maps.get(concept.lower(), self.concept_maps["truth"])
        
        # Extract parameters
        concept_harmonics = concept_params["harmonics"]
        rhythm = concept_params["rhythm"]
        balance = concept_params["balance"]
        
        # Frequency calculation
        frequencies = [self.base_frequency * h for h in concept_harmonics]
        
        # Amplitude based on balance
        amplitudes = []
        for i in range(len(frequencies)):
            # Use balance values cyclically
            balance_index = i % len(balance)
            amplitudes.append(balance[balance_index])
        
        # Phase calculation based on rhythm
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
            concept_type="abstract",
            metadata={
                "concept": concept,
                "related_concepts": self._find_related_concepts(concept)
            }
        )
    
    def _find_related_concepts(self, concept: str) -> List[str]:
        """Find concepts related to the given concept."""
        # Simple implementation - in production would be more sophisticated
        concept_relations = {
            "truth": ["honesty", "accuracy", "reality"],
            "connection": ["relationship", "bond", "link"],
            "growth": ["development", "evolution", "progress"],
            "balance": ["harmony", "equilibrium", "stability"],
            "creativity": ["innovation", "imagination", "originality"]
        }
        
        return concept_relations.get(concept.lower(), [])
    
    def wave_to_visualization(self, wave: WavePattern) -> Dict[str, Any]:
        """Convert a wave pattern to visualization data."""
        # Generate time points - 100 points over the duration
        time_points = np.linspace(0, wave.duration, 100)
        
        # Calculate the waveform at each time point
        waveform = np.zeros_like(time_points)
        
        for amp, freq, phase in zip(wave.amplitudes, wave.frequencies, wave.phases):
            # Repeat amplitude for all time points if it's a single value
            if not isinstance(amp, (list, np.ndarray)):
                amplitude = np.ones_like(time_points) * amp
            else:
                # Interpolate if we have multiple amplitude values
                amplitude = np.interp(
                    time_points, 
                    np.linspace(0, wave.duration, len(amp)), 
                    amp
                )
            
            # Add this frequency component to the waveform
            waveform += amplitude * np.sin(2 * np.pi * freq * time_points + phase)
        
        # Normalize waveform to -1 to 1 range if it exceeds that
        if np.max(np.abs(waveform)) > 1.0:
            waveform = waveform / np.max(np.abs(waveform))
        
        # Create visualization data
        visualization = {
            "pattern_id": wave.pattern_id,
            "time_points": time_points.tolist(),
            "waveform": waveform.tolist(),
            "frequencies": wave.frequencies,
            "concept_type": wave.concept_type,
            "metadata": wave.metadata
        }
        
        return visualization
    
    def wave_to_audio(self, wave: WavePattern) -> Dict[str, Any]:
        """Convert a wave pattern to audio parameters."""
        # Sample rate for audio generation
        sample_rate = 44100
        
        # Generate time points at audio sample rate
        time_points = np.linspace(0, wave.duration, int(wave.duration * sample_rate))
        
        # Calculate the waveform at each time point
        waveform = np.zeros_like(time_points)
        
        for amp, freq, phase in zip(wave.amplitudes, wave.frequencies, wave.phases):
            # Repeat amplitude for all time points if it's a single value
            if not isinstance(amp, (list, np.ndarray)):
                amplitude = np.ones_like(time_points) * amp
            else:
                # Interpolate if we have multiple amplitude values
                amplitude = np.interp(
                    time_points, 
                    np.linspace(0, wave.duration, len(amp)), 
                    amp
                )
            
            # Add this frequency component to the waveform
            waveform += amplitude * np.sin(2 * np.pi * freq * time_points + phase)
        
        # Normalize waveform to -1 to 1 range if it exceeds that
        if np.max(np.abs(waveform)) > 1.0:
            waveform = waveform / np.max(np.abs(waveform))
        
        # In a production system, this would generate an actual audio file
        # Here we'll just return the parameters needed for audio generation
        
        # Create audio data (returning only first 1000 samples to keep response size reasonable)
        audio_data = {
            "pattern_id": wave.pattern_id,
            "sample_rate": sample_rate,
            "frequencies": wave.frequencies,
            "duration": wave.duration,
            "waveform_sample": waveform[:1000].tolist(),  # Just a sample for demonstration
            "metadata": wave.metadata
        }
        
        return audio_data
    
    def blend_waves(self, waves: List[WavePattern]) -> WavePattern:
        """Blend multiple wave patterns into a single harmonious pattern."""
        if not waves:
            raise ValueError("No waves provided for blending")
        
        if len(waves) == 1:
            return waves[0]
        
        # Create a new pattern ID
        pattern_id = str(uuid.uuid4())
        
        # Determine the longest duration
        max_duration = max(wave.duration for wave in waves)
        
        # Collect all frequencies and sort by golden ratio proximity
        all_freqs = []
        for wave in waves:
            all_freqs.extend(wave.frequencies)
        
        # Remove duplicates by clustering similar frequencies
        # (in production this would be more sophisticated)
        unique_freqs = []
        for freq in sorted(all_freqs):
            # Check if this frequency is already represented
            if not unique_freqs or min(abs(freq/uf - 1) for uf in unique_freqs) > 0.05:
                unique_freqs.append(freq)
        
        # Sort by proximity to golden ratio multiples of base frequency
        base = min(unique_freqs)
        ratio_proximity = [min(abs(freq/(base*PHI**i) - 1) for i in range(-5, 6)) for freq in unique_freqs]
        sorted_freqs = [f for _, f in sorted(zip(ratio_proximity, unique_freqs))]
        
        # Calculate new amplitudes based on wave contributions
        amplitudes = [0] * len(sorted_freqs)
        for wave in waves:
            for i, freq in enumerate(sorted_freqs):
                # Find the closest matching frequency in this wave
                closest_index = None
                closest_diff = float('inf')
                for j, wave_freq in enumerate(wave.frequencies):
                    diff = abs(freq/wave_freq - 1)
                    if diff < closest_diff and diff < 0.05:  # Within 5%
                        closest_diff = diff
                        closest_index = j
                
                # If we found a match, add its amplitude to our blended amplitudes
                if closest_index is not None:
                    # Use first amplitude if it's a list
                    amp = wave.amplitudes[closest_index]
                    if isinstance(amp, (list, np.ndarray)):
                        amp = amp[0]
                    amplitudes[i] += amp / len(waves)  # Average across waves
        
        # Create phases that maximize harmony
        # In Bach's music, phases often follow golden ratio relationships
        phases = [(i * 2 * math.pi * (1/PHI)) % (2 * math.pi) for i in range(len(sorted_freqs))]
        
        # Create the blended wave pattern
        return WavePattern(
            pattern_id=pattern_id,
            amplitudes=amplitudes,
            frequencies=sorted_freqs,
            phases=phases,
            harmonics=[f/base for f in sorted_freqs],  # Express as ratios to base
            duration=max_duration,
            concept_type="blend",
            metadata={
                "source_patterns": [wave.pattern_id for wave in waves],
                "source_concepts": [wave.metadata.get("concept", wave.metadata.get("text_sample", "unknown")) 
                                   for wave in waves]
            }
        )

# Create singleton instance
communicator = WaveCommunicator()