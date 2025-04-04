#!/usr/bin/env python3

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import components
from harmony.orchestrator import orchestrator
from wave.communicator import communicator as wave_communicator
from patterns.extractor import extractor as pattern_extractor
from visualization.multi_sensory import visualizer

async def run_tests():
    print("\n===== The Conductor: System Test =====\n")
    
    # Test text processing
    text = """The Conductor Framework must prioritize mathematical patterns as the essence of ideas, not merely as representations. 
    By following Bach's mathematical structure and the golden ratio, we create a system that embodies harmony and truth.
    This approach enables a new form of communication that transcends the limitations of symbolic language."""
    
    print("Processing text through orchestrator...")
    result = await orchestrator.process_text(text)
    print(f"Harmony Index: {result['harmony_index']}\n")
    print(f"Pattern Counts: {result['metadata']['pattern_types']}\n")
    
    # Test wave communication
    print("\n===== Wave-Based Communication Test =====\n")
    wave = wave_communicator.text_to_wave(text)
    print(f"Wave Pattern ID: {wave.pattern_id}")
    print(f"Frequencies: {wave.frequencies[:3]}...")
    print(f"Duration: {wave.duration}")
    
    # Test concept visualization
    print("\n===== Concept Visualization Test =====\n")
    concepts = ["truth", "connection", "growth", "balance", "creativity"]
    
    for concept in concepts:
        print(f"\nGenerating visualization for concept: {concept}")
        pattern = await orchestrator.generate_multi_sensory_pattern(concept)
        print(f"Wave frequencies: {pattern['wave']['frequencies'][:3]}...")
        print(f"Related concepts: {pattern['related_concepts']}")
    
    # Test AI bridge
    print("\n===== AI Bridge Communication Test =====\n")
    bridge_message = "Mathematical patterns serve as the foundation of our communication system."
    bridge_result = await orchestrator.communicate_between_models(
        "claude", "grok", bridge_message, "Mathematical Communication"
    )
    print(f"Message Protocol: {bridge_result['protocol']}")
    print(f"Harmony Index: {bridge_result['harmony_index']}")
    
    print("\n===== Test Complete =====\n")
    print("The Conductor framework is operational and harmonious.")

if __name__ == "__main__":
    asyncio.run(run_tests())