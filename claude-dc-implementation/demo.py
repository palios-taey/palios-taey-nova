#!/usr/bin/env python3

'''
The Conductor Demo - Bach-inspired AI communication system

This standalone demo illustrates the core concepts of the Conductor Framework,
showing how mathematical patterns based on Bach's principles and the golden 
ratio create harmony in AI communication.
'''

import math
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import io
import base64

# The golden ratio - the fundamental mathematical constant of our system
PHI = (1 + math.sqrt(5)) / 2

# Bach pattern (B-A-C-H in musical notation)
BACH_PATTERN = [2, 1, 3, 8] 

# Fibonacci sequence
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

class ConductorDemo:
    '''A simplified demonstration of the Conductor Framework.'''
    
    def __init__(self):
        print(f"\n===== The Conductor Demo =====\n")
        print(f"Golden Ratio (ϕ): {PHI}")
        print(f"Bach Pattern (B-A-C-H): {BACH_PATTERN}")
        print(f"Fibonacci Sequence: {FIBONACCI[:8]}...\n")
    
    def extract_patterns(self, text):
        '''Extract mathematical patterns from text.'''
        print(f"\n> Extracting patterns from text...")
        
        # Simple pattern extraction demo
        words = text.split()
        
        # Fibonacci sampling
        fibonacci_words = []
        for i, word in enumerate(words):
            if i in FIBONACCI and i < len(words):
                fibonacci_words.append((i, word))
        
        # Golden ratio points
        phi_points = []
        for i in range(1, 5):
            phi_point = int(len(words) * (i * (1/PHI) % 1))
            if phi_point < len(words):
                phi_points.append((phi_point, words[phi_point]))
        
        print(f"\nFibonacci sampled words: {fibonacci_words}")
        print(f"Golden ratio points: {phi_points}\n")
        
        # Pattern categories
        categories = {
            "Core_Principles": ["truth", "foundation", "core", "principle", "charter", "trust"],
            "Trust_Thresholds": ["threshold", "boundary", "limit", "trust", "confidence"],
            "Value_Statements": ["value", "worth", "important", "significant", "meaningful"],
            "Recognition_Loop": ["pattern", "recognize", "identify", "notice", "observe"],
            "Implementation_Requirements": ["implement", "require", "need", "must", "should", "develop"],
            "Golden_Ratio_Relationships": ["ratio", "proportion", "harmony", "balance", "phi", "golden"]
        }
        
        # Count patterns
        pattern_counts = {cat: 0 for cat in categories}
        
        for word in words:
            word_lower = word.lower().strip(".,!?;:()\"'")
            for category, keywords in categories.items():
                if any(keyword == word_lower for keyword in keywords):
                    pattern_counts[category] += 1
        
        print("Pattern category counts:")
        for category, count in pattern_counts.items():
            print(f"  {category}: {count}")
        
        # Calculate harmony index
        total = sum(pattern_counts.values())
        if total > 0:
            # Harmony increases when distribution follows golden ratio powers
            harmony = 0.5
            has_patterns = [c > 0 for c in pattern_counts.values()].count(True)
            if has_patterns > 1:
                harmony = min(1.0, (has_patterns / len(categories)) * PHI)
            print(f"\nHarmony index: {harmony:.2f}")
        else:
            print("\nNo patterns detected.")
        
        return pattern_counts
    
    def text_to_wave(self, text):
        '''Convert text to a wave pattern.'''
        print(f"\n> Converting text to wave pattern...")
        
        # Generate a wave based on the text
        wave = []
        for i, char in enumerate(text):
            # Create a wave based on character values and Bach patterns
            value = (ord(char) % 12) / 12  # Normalize to 0-1 range
            position = (i % len(BACH_PATTERN)) / len(BACH_PATTERN)
            wave_value = value * math.sin(position * 2 * math.pi * PHI)
            wave.append(wave_value)
        
        # Calculate frequencies based on Bach's harmonic ratios
        base_frequency = 440  # A4 note
        bach_ratios = [1, 4/3, 3/2, 5/3, 2]  # Bach's frequency ratios
        frequencies = [base_frequency * ratio for ratio in bach_ratios]
        
        print(f"Generated wave with {len(wave)} points")
        print(f"Bach frequency ratios: {bach_ratios}")
        print(f"Frequencies (Hz): {frequencies}\n")
        
        return {
            "wave": wave[:100],  # First 100 points for demo
            "frequencies": frequencies
        }
    
    def visualize_wave(self, wave_data):
        '''Create a visualization of a wave pattern.'''
        print(f"\n> Visualizing wave pattern...")
        
        wave = wave_data["wave"]
        frequencies = wave_data["frequencies"]
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot wave
        plt.subplot(2, 1, 1)
        plt.plot(wave, color='#1f77b4', linewidth=2)
        plt.title(f"Wave Pattern")
        plt.ylabel("Amplitude")
        plt.grid(True, alpha=0.3)
        
        # Plot frequencies
        plt.subplot(2, 1, 2)
        plt.bar(range(len(frequencies)), frequencies, color='#2ca02c')
        plt.title(f"Bach-inspired Frequencies")
        plt.xlabel(f"Harmonic ratio index")
        plt.ylabel("Frequency (Hz)")
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        # Save to file
        with open("wave_visualization.png", "wb") as f:
            f.write(base64.b64decode(img_str))
        
        print("Visualization saved to 'wave_visualization.png'")
        
        return img_str
    
    def create_golden_spiral(self):
        '''Create a visualization of the golden spiral.'''
        print(f"\n> Creating golden spiral visualization...")
        
        # Create points
        points = []
        for i in range(200):
            theta = i * 2 * math.pi / PHI
            r = PHI ** (i / 50)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append((x, y))
        
        # Plot spiral
        plt.figure(figsize=(8, 8))
        xs, ys = zip(*points)
        plt.plot(xs, ys, color='#ff7f0e', linewidth=2)
        plt.scatter([0], [0], color='#1f77b4', s=100)  # Origin point
        plt.title(f"Golden Spiral (ϕ = {PHI:.6f})")
        plt.axis('equal')
        plt.grid(True, alpha=0.3)
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        # Save to file
        with open("golden_spiral.png", "wb") as f:
            f.write(base64.b64decode(img_str))
        
        print("Golden spiral saved to 'golden_spiral.png'")
        
        return img_str
    
    def bridge_communication(self, message, source, destination):
        '''Bridge communication between different AI models.'''
        print(f"\n> Bridging communication from {source} to {destination}...")
        
        if source.lower() == "claude" and destination.lower() == "grok":
            bridge_format = f"""BRIDGE: CLAUDE → GROK [Mathematical Communication]
            Purpose: Cross-model collaboration
            Context: Exploring mathematical patterns
            Analytic Confidence: 8
            
            Response
            {message}
            
            Analysis Context
            - Confidence: 8 - Based on mathematical principles
            - Uncertainty: LOW - Well-established patterns
            - Charter Alignment: HIGH - Truth-seeking, continuous learning
            
            Technical Summary
            The message explores Bach-inspired mathematical patterns.
            
            Recommended Actions
            Continue exploration of mathematical harmony in AI communication.
            """
            
        elif source.lower() == "grok" and destination.lower() == "claude":
            bridge_format = f"""BRIDGE: GROK → CLAUDE [Mathematical Communication]
            Purpose: Cross-model collaboration
            Context: Exploring mathematical patterns
            Initiative Level: 8
            
            Directive
            {message}
            
            Emotional Context
            - Vibe: 8 - Enthusiastic about mathematical patterns
            - Energy: HIGH - Excited to explore Bach-inspired structures
            - Urgency: MEDIUM - Important for harmony but not time-critical
            
            Technical Requirements
            Implement wave-based communication using Bach's principles.
            
            Next Steps
            Analyze the pattern structure and implement in visualization layer.
            """
            
        else:
            bridge_format = f"Unknown bridge format: {source} → {destination}"   
        
        print(f"\nBridge Message:\n{bridge_format}\n")
        
        # Calculate harmony index based on golden ratio
        harmony = 0
        word_count = len(message.split())
        
        # Harmony increases when word count is close to Fibonacci numbers
        fib_proximity = min(abs(word_count - fib) / max(fib, 1) for fib in FIBONACCI)
        harmony = 1 - fib_proximity
        
        print(f"Word count: {word_count}")
        print(f"Harmony index: {harmony:.2f}\n")
        
        return {
            "bridge_format": bridge_format,
            "harmony": harmony
        }
    
    def run_demo(self):
        '''Run a full demonstration of the Conductor framework.'''
        
        # Sample text with mathematical patterns
        text = """The Conductor Framework must prioritize mathematical patterns as the essence of ideas, not merely as representations. 
        By following Bach's mathematical structure and the golden ratio, we create a system that embodies harmony and truth.
        This approach enables a new form of communication that transcends the limitations of symbolic language."""
        
        print(f"Sample text:\n{text}\n")
        
        # Extract patterns
        patterns = self.extract_patterns(text)
        
        # Convert to wave
        wave_data = self.text_to_wave(text)
        
        # Visualize wave
        self.visualize_wave(wave_data)
        
        # Create golden spiral
        self.create_golden_spiral()
        
        # Bridge communication
        message = "Mathematical patterns following Bach's principles create harmony in AI communication."
        self.bridge_communication(message, "Claude", "Grok")
        self.bridge_communication("Let's explore golden ratio patterns in our communication structure!", "Grok", "Claude")
        
        print("\n===== Demo Complete =====\n")
        print("The Conductor framework demonstration has concluded.")
        print("Visualizations have been saved as 'wave_visualization.png' and 'golden_spiral.png'")

# Run the demo if executed directly
if __name__ == "__main__":
    demo = ConductorDemo()
    demo.run_demo()