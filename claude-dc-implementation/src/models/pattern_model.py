#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Pattern Model
----------------------------------
This module implements mathematical pattern recognition models,
treating patterns AS ideas rather than merely representations of ideas.

The implementation follows mathematical principles from Bach's compositions
and the golden ratio, creating a harmonious structure for pattern detection.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import pywt
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union

# Load configuration
CONFIG_PATH = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/config/conductor_config.json")
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

class PatternModel:
    """
    Mathematical pattern recognition model implementing the Conductor Framework.
    
    This model treats patterns as the essence of ideas, using mathematical structures
    derived from Bach's compositions and golden ratio proportions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the pattern model with configuration.
        
        Args:
            config: Configuration dictionary (defaults to loaded CONFIG if None)
        """
        self.config = config or CONFIG
        self.golden_ratio = self.config["mathematical_patterns"]["golden_ratio"]
        self.fibonacci_sequence = self.config["mathematical_patterns"]["fibonacci_sequence"]
        self.bach_structures = self.config["mathematical_patterns"]["bach_structures"]
        self.wave_parameters = self.config["mathematical_patterns"]["wave_parameters"]
        
        # Initialize model components
        self.embedding_model = None
        self.pattern_classifier = None
        self.wavelet_transformer = None
        
        # Initialize pattern spaces
        self.pattern_embeddings = {}
        self.pattern_clusters = {}
        
        # Setup model architecture
        self._setup_models()
    
    def _setup_models(self) -> None:
        """Set up the pattern recognition model architecture."""
        # Set up the embedding model (encoder)
        input_layer = layers.Input(shape=(300,))  # Assuming 300-dim word vectors
        
        # Create a Bach-inspired architecture with golden ratio proportions
        # The network has a structure that mirrors the mathematical properties of Bach's music
        units_1 = int(300 / self.golden_ratio)  # First layer size
        units_2 = int(units_1 / self.golden_ratio)  # Second layer size
        units_3 = int(units_2 / self.golden_ratio)  # Third layer size
        
        # Encoder layers with proportions based on golden ratio
        x = layers.Dense(units_1, activation='relu')(input_layer)
        x = layers.Dense(units_2, activation='relu')(x)
        x = layers.Dense(units_3, activation='relu')(x)
        
        # Bottleneck layer (latent space)
        latent = layers.Dense(21, activation='relu')(x)  # 21 = Fibonacci number
        
        # Decoder layers with reverse structure
        x = layers.Dense(units_3, activation='relu')(latent)
        x = layers.Dense(units_2, activation='relu')(x)
        x = layers.Dense(units_1, activation='relu')(x)
        output_layer = layers.Dense(300, activation='linear')(x)
        
        # Create autoencoder model
        self.embedding_model = models.Model(input_layer, latent, name="pattern_encoder")
        self.autoencoder = models.Model(input_layer, output_layer, name="pattern_autoencoder")
        
        # Compile autoencoder
        self.autoencoder.compile(optimizer='adam', loss='mse')
        
        # Create pattern classifier
        classifier_input = layers.Input(shape=(21,))  # Using the latent space size
        x = layers.Dense(13, activation='relu')(classifier_input)  # 13 = Fibonacci number
        x = layers.Dense(8, activation='relu')(x)  # 8 = Fibonacci number
        pattern_output = layers.Dense(len(self.config["transcript_processing"]["pattern_classes"]), 
                                    activation='softmax')(x)
        
        self.pattern_classifier = models.Model(classifier_input, pattern_output, name="pattern_classifier")
        self.pattern_classifier.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        
        # Set up wavelet transformer for frequency-domain pattern analysis
        self.wavelet_name = 'db4'  # Daubechies wavelet (similar to musical patterns)
        self.wavelet_level = 5  # Decomposition level
    
    def wavelet_transform(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Apply wavelet transform to convert data to frequency domain.
        
        Args:
            data: Input data as numpy array
            
        Returns:
            Dictionary of wavelet coefficients
        """
        if data.ndim == 1:
            # For 1D data (like time series)
            coeffs = pywt.wavedec(data, self.wavelet_name, level=self.wavelet_level)
            return {f"level_{i}": coef for i, coef in enumerate(coeffs)}
        else:
            # For 2D data (like embeddings)
            coeffs = pywt.wavedec2(data, self.wavelet_name, level=self.wavelet_level)
            return {f"level_{i}": coef for i, coef in enumerate(coeffs)}
    
    def inverse_wavelet_transform(self, coeffs: List[np.ndarray], original_shape: Tuple[int, ...]) -> np.ndarray:
        """
        Apply inverse wavelet transform to reconstruct data.
        
        Args:
            coeffs: Wavelet coefficients
            original_shape: Shape of the original data
            
        Returns:
            Reconstructed data as numpy array
        """
        if len(original_shape) == 1:
            # For 1D data
            return pywt.waverec(coeffs, self.wavelet_name)
        else:
            # For 2D data
            return pywt.waverec2(coeffs, self.wavelet_name)
    
    def pattern_to_wavelet(self, pattern_embedding: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Convert pattern embedding to wavelet domain.
        
        Args:
            pattern_embedding: Pattern embedding vector
            
        Returns:
            Dictionary of wavelet coefficients
        """
        return self.wavelet_transform(pattern_embedding)
    
    def wavelet_to_pattern(self, wavelet_coeffs: Dict[str, np.ndarray], original_shape: Tuple[int, ...]) -> np.ndarray:
        """
        Convert wavelet coefficients back to pattern embedding.
        
        Args:
            wavelet_coeffs: Dictionary of wavelet coefficients
            original_shape: Shape of the original embedding
            
        Returns:
            Reconstructed pattern embedding
        """
        coeffs_list = [wavelet_coeffs[f"level_{i}"] for i in range(len(wavelet_coeffs))]
        return self.inverse_wavelet_transform(coeffs_list, original_shape)
    
    def encode_pattern(self, pattern_data: np.ndarray) -> np.ndarray:
        """
        Encode pattern data into the latent space.
        
        Args:
            pattern_data: Input pattern data
            
        Returns:
            Encoded pattern in latent space
        """
        if self.embedding_model is None:
            raise ValueError("Model not initialized")
            
        # Reshape input if needed
        if pattern_data.ndim == 1:
            pattern_data = pattern_data.reshape(1, -1)
            
        # Encode to latent space
        return self.embedding_model.predict(pattern_data)
    
    def classify_pattern(self, pattern_embedding: np.ndarray) -> Dict[str, float]:
        """
        Classify pattern embedding into pattern classes.
        
        Args:
            pattern_embedding: Pattern embedding in latent space
            
        Returns:
            Dictionary mapping pattern classes to probabilities
        """
        if self.pattern_classifier is None:
            raise ValueError("Pattern classifier not initialized")
            
        # Reshape input if needed
        if pattern_embedding.ndim == 1:
            pattern_embedding = pattern_embedding.reshape(1, -1)
            
        # Get predictions
        predictions = self.pattern_classifier.predict(pattern_embedding)[0]
        
        # Map predictions to pattern classes
        pattern_classes = list(self.config["transcript_processing"]["pattern_classes"].keys())
        return {cls: float(pred) for cls, pred in zip(pattern_classes, predictions)}
    
    def generate_pattern_embedding_space(self, pattern_data: Dict[str, List[np.ndarray]]) -> Dict[str, Any]:
        """
        Generate a pattern embedding space from multiple pattern examples.
        
        Args:
            pattern_data: Dictionary mapping pattern types to lists of pattern data
            
        Returns:
            Dictionary containing the pattern embedding space
        """
        # Encode all patterns
        embeddings = {}
        all_embeddings = []
        pattern_labels = []
        
        for pattern_type, data_list in pattern_data.items():
            type_embeddings = []
            for data in data_list:
                # Encode the pattern
                embedding = self.encode_pattern(data)[0]  # Get the first (only) embedding
                type_embeddings.append(embedding)
                all_embeddings.append(embedding)
                pattern_labels.append(pattern_type)
                
            embeddings[pattern_type] = np.array(type_embeddings)
            
        # Combine all embeddings
        all_embeddings = np.array(all_embeddings)
        
        # Apply dimensionality reduction for visualization
        tsne = TSNE(n_components=2, random_state=42)
        reduced_embeddings = tsne.fit_transform(all_embeddings)
        
        # Create the pattern space
        pattern_space = {
            "embeddings": embeddings,
            "all_embeddings": all_embeddings,
            "reduced_embeddings": reduced_embeddings,
            "labels": pattern_labels,
            "tsne_model": tsne
        }
        
        self.pattern_embeddings = pattern_space
        return pattern_space
    
    def find_pattern_relationships(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        Find relationships between different pattern types based on their embeddings.
        
        Returns:
            Dictionary mapping pattern types to related patterns with similarity scores
        """
        relationships = {}
        
        # Ensure we have pattern embeddings
        if not self.pattern_embeddings or "embeddings" not in self.pattern_embeddings:
            return relationships
            
        pattern_types = list(self.pattern_embeddings["embeddings"].keys())
        
        # Calculate centroids for each pattern type
        centroids = {}
        for pattern_type, embeddings in self.pattern_embeddings["embeddings"].items():
            if len(embeddings) > 0:
                centroids[pattern_type] = np.mean(embeddings, axis=0)
        
        # Calculate similarities between pattern centroids
        for pattern1 in pattern_types:
            if pattern1 not in centroids:
                continue
                
            relationships[pattern1] = []
            centroid1 = centroids[pattern1]
            
            for pattern2 in pattern_types:
                if pattern2 == pattern1 or pattern2 not in centroids:
                    continue
                    
                centroid2 = centroids[pattern2]
                
                # Calculate cosine similarity
                similarity = np.dot(centroid1, centroid2) / (np.linalg.norm(centroid1) * np.linalg.norm(centroid2))
                
                relationships[pattern1].append((pattern2, float(similarity)))
            
            # Sort relationships by similarity (descending)
            relationships[pattern1].sort(key=lambda x: x[1], reverse=True)
        
        return relationships
    
    def pattern_to_frequency(self, pattern_embedding: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Convert pattern embedding to frequency domain representation.
        
        This is key for the pattern-to-audio mapping in the visualization.
        
        Args:
            pattern_embedding: Pattern embedding vector
            
        Returns:
            Dictionary of frequency components
        """
        # Apply wavelet transform for time-frequency analysis
        wavelet_coeffs = self.pattern_to_wavelet(pattern_embedding)
        
        # Extract frequency information at different scales
        frequencies = {}
        
        for level, coeffs in wavelet_coeffs.items():
            if isinstance(coeffs, tuple):
                # For 2D wavelets, coeffs is a tuple of (cA, (cH, cV, cD))
                frequencies[f"{level}_approximation"] = coeffs[0] if len(coeffs) > 0 else np.array([])
                if len(coeffs) > 1:
                    frequencies[f"{level}_horizontal"] = coeffs[1][0] if len(coeffs[1]) > 0 else np.array([])
                    frequencies[f"{level}_vertical"] = coeffs[1][1] if len(coeffs[1]) > 1 else np.array([])
                    frequencies[f"{level}_diagonal"] = coeffs[1][2] if len(coeffs[1]) > 2 else np.array([])
            else:
                # For 1D wavelets
                frequencies[level] = coeffs
        
        return frequencies
    
    def generate_audio_parameters(self, pattern_embedding: np.ndarray) -> Dict[str, Any]:
        """
        Generate audio parameters from pattern embedding for sonification.
        
        Args:
            pattern_embedding: Pattern embedding vector
            
        Returns:
            Dictionary of audio parameters
        """
        # Convert to frequency domain
        frequencies = self.pattern_to_frequency(pattern_embedding)
        
        # Extract key audio parameters using Bach-inspired harmonics
        harmonic_ratios = self.wave_parameters["harmonic_ratios"]
        
        # Calculate base frequency (fundamental)
        # Map the first principal component to a musical range (110Hz - 440Hz)
        fundamental = 110 + (440 - 110) * (np.mean(pattern_embedding) + 1) / 2
        
        # Generate harmonics
        harmonics = [fundamental * ratio for ratio in harmonic_ratios]
        
        # Extract amplitude envelope from embedding
        if len(pattern_embedding) >= 4:
            # Use first 4 dimensions for ADSR envelope (Attack, Decay, Sustain, Release)
            adsr = pattern_embedding[:4]
            adsr = (adsr - adsr.min()) / (adsr.max() - adsr.min() + 1e-10)  # Normalize to [0,1]
        else:
            adsr = np.array([0.1, 0.2, 0.7, 0.5])  # Default ADSR
        
        # Map wavelet coefficients to modulation parameters
        modulation = {}
        for level, coeffs in frequencies.items():
            if isinstance(coeffs, np.ndarray) and coeffs.size > 0:
                # Use coefficient energy as modulation intensity
                energy = np.mean(np.abs(coeffs))
                modulation[level] = float(energy)
        
        # Golden ratio-based timing parameters
        timing = {
            "beat_duration": 60 / (self.golden_ratio * 60),  # BPM based on golden ratio
            "pattern_duration": 1 + self.golden_ratio,  # Duration in seconds
            "phrase_structure": [1, 1, 2, 3, 5, 8]  # Fibonacci sequence for phrase structure
        }
        
        return {
            "fundamental": float(fundamental),
            "harmonics": [float(h) for h in harmonics],
            "adsr": [float(a) for a in adsr],
            "modulation": modulation,
            "timing": timing
        }
    
    def save_model(self, model_dir: str) -> None:
        """
        Save the pattern model to disk.
        
        Args:
            model_dir: Directory to save the model
        """
        os.makedirs(model_dir, exist_ok=True)
        
        # Save model architectures
        if self.embedding_model:
            self.embedding_model.save(os.path.join(model_dir, "embedding_model"))
            
        if self.pattern_classifier:
            self.pattern_classifier.save(os.path.join(model_dir, "pattern_classifier"))
            
        if self.autoencoder:
            self.autoencoder.save(os.path.join(model_dir, "autoencoder"))
        
        # Save configuration
        with open(os.path.join(model_dir, "model_config.json"), 'w') as f:
            json.dump({
                "golden_ratio": self.golden_ratio,
                "fibonacci_sequence": self.fibonacci_sequence,
                "wavelet_name": self.wavelet_name,
                "wavelet_level": self.wavelet_level,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"Model saved to {model_dir}")
    
    def load_model(self, model_dir: str) -> None:
        """
        Load the pattern model from disk.
        
        Args:
            model_dir: Directory containing the saved model
        """
        # Load model architectures
        if os.path.exists(os.path.join(model_dir, "embedding_model")):
            self.embedding_model = tf.keras.models.load_model(os.path.join(model_dir, "embedding_model"))
            
        if os.path.exists(os.path.join(model_dir, "pattern_classifier")):
            self.pattern_classifier = tf.keras.models.load_model(os.path.join(model_dir, "pattern_classifier"))
            
        if os.path.exists(os.path.join(model_dir, "autoencoder")):
            self.autoencoder = tf.keras.models.load_model(os.path.join(model_dir, "autoencoder"))
        
        # Load configuration
        if os.path.exists(os.path.join(model_dir, "model_config.json")):
            with open(os.path.join(model_dir, "model_config.json"), 'r') as f:
                config = json.load(f)
                self.wavelet_name = config.get("wavelet_name", self.wavelet_name)
                self.wavelet_level = config.get("wavelet_level", self.wavelet_level)
        
        print(f"Model loaded from {model_dir}")
    
    def pattern_to_visual_parameters(self, pattern_embedding: np.ndarray) -> Dict[str, Any]:
        """
        Convert pattern embedding to visual parameters for visualization.
        
        Args:
            pattern_embedding: Pattern embedding vector
            
        Returns:
            Dictionary of visual parameters
        """
        # Apply PCA to reduce to essential components
        if pattern_embedding.ndim == 1:
            pattern_embedding = pattern_embedding.reshape(1, -1)
            
        if pattern_embedding.shape[1] > 3:
            pca = PCA(n_components=3)
            reduced = pca.fit_transform(pattern_embedding)[0]
        else:
            reduced = pattern_embedding[0]
        
        # Map to HSL color space (Hue, Saturation, Lightness)
        # Hue: first component mapped to [0, 360]
        # Saturation: second component mapped to [0, 100]
        # Lightness: third component mapped to [20, 80]
        hue = ((reduced[0] + 1) / 2) * 360  # Map [-1,1] to [0,360]
        saturation = ((reduced[1] + 1) / 2) * 100  # Map [-1,1] to [0,100]
        
        # Use third component, or golden ratio if not available
        if len(reduced) > 2:
            lightness = 20 + ((reduced[2] + 1) / 2) * 60  # Map [-1,1] to [20,80]
        else:
            lightness = 20 + (self.golden_ratio / 3) * 60
        
        # Calculate proportions based on golden ratio
        width_ratio = self.golden_ratio
        height_ratio = 1 / self.golden_ratio
        
        # Generate shapes based on wavelet decomposition
        frequency_data = self.pattern_to_frequency(pattern_embedding[0])
        shapes = []
        
        # Use wavelet coefficients to define shapes
        for i, (level, coeffs) in enumerate(frequency_data.items()):
            if isinstance(coeffs, np.ndarray) and coeffs.size > 0:
                # Calculate shape parameters from coefficients
                energy = np.mean(np.abs(coeffs))
                size = 10 + 90 * energy  # Size from 10 to 100
                opacity = 0.3 + 0.7 * energy  # Opacity from 0.3 to 1.0
                
                # Position based on golden ratio grid
                x_position = (i % 3) * (100 / 3)
                y_position = (i // 3) * (100 / 3)
                
                shapes.append({
                    "type": "circle" if i % 2 == 0 else "rectangle",
                    "size": float(size),
                    "position": [float(x_position), float(y_position)],
                    "color": f"hsla({hue:.1f}, {saturation:.1f}%, {lightness:.1f}%, {opacity:.2f})",
                    "rotation": float(i * 137.5)  # Golden angle in degrees
                })
        
        return {
            "color": {
                "hue": float(hue),
                "saturation": float(saturation),
                "lightness": float(lightness),
                "hex": f"hsl({hue:.1f}, {saturation:.1f}%, {lightness:.1f}%)"
            },
            "proportions": {
                "width_ratio": float(width_ratio),
                "height_ratio": float(height_ratio),
                "golden_sections": [0, 38.2, 61.8, 100]  # Golden section percentages
            },
            "shapes": shapes,
            "patterns": {
                "fibonacci_spiral": True,
                "golden_rectangles": True,
                "wave_patterns": len(shapes) > 0
            }
        }


if __name__ == "__main__":
    # Example usage
    model = PatternModel()
    
    # Generate random pattern data for testing
    np.random.seed(42)
    pattern_data = {
        "Core_Principles": [np.random.rand(300) for _ in range(5)],
        "Value_Statements": [np.random.rand(300) for _ in range(5)],
        "Recognition_Loop": [np.random.rand(300) for _ in range(5)]
    }
    
    # Generate pattern space
    pattern_space = model.generate_pattern_embedding_space(pattern_data)
    print(f"Generated pattern space with {pattern_space['all_embeddings'].shape[0]} embeddings")
    
    # Find pattern relationships
    relationships = model.find_pattern_relationships()
    for pattern_type, related in relationships.items():
        print(f"\n{pattern_type} is related to:")
        for related_type, similarity in related:
            print(f"  - {related_type} (similarity: {similarity:.2f})")
    
    # Generate audio parameters for a sample pattern
    sample_pattern = pattern_data["Core_Principles"][0]
    audio_params = model.generate_audio_parameters(sample_pattern)
    print("\nAudio parameters:")
    print(f"  Fundamental frequency: {audio_params['fundamental']:.2f} Hz")
    print(f"  Harmonics: {', '.join([f'{h:.2f} Hz' for h in audio_params['harmonics']])}")
    
    # Generate visual parameters
    visual_params = model.pattern_to_visual_parameters(sample_pattern.reshape(1, -1))
    print("\nVisual parameters:")
    print(f"  Color: {visual_params['color']['hex']}")
    print(f"  Golden ratio sections: {visual_params['proportions']['golden_sections']}")
    print(f"  Number of shapes: {len(visual_params['shapes'])}")
    
    # Save model
    model.save_model("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/models/pattern_model")