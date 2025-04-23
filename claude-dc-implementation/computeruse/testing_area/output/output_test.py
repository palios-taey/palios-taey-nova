#!/usr/bin/env python3
"""
Extended Output Test (128K)
Tests Claude's extended output capabilities up to 128K tokens.
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extended_output_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.extended_output')

# Import required libraries
from anthropic import Anthropic

def get_api_key():
    """Get Anthropic API key from environment or file."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
            logger.info("Found API key in ~/.anthropic/api_key")
        else:
            raise ValueError("API key not found")
    return api_key

async def test_extended_output():
    """Test extended output capabilities."""
    logger.info("Starting extended output test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    logger.info("Created Anthropic client")
    
    # Set up a prompt that will generate a very long response
    prompt = """
    Please write an extremely detailed explanation of machine learning, 
    covering all major algorithms, techniques, and applications.
    Include sections on:
    1. Supervised Learning (with detailed explanations of regression, classification, neural networks, SVMs, etc.)
    2. Unsupervised Learning (clustering, dimensionality reduction, etc.)
    3. Reinforcement Learning
    4. Deep Learning (CNN, RNN, Transformers, etc.)
    5. Natural Language Processing
    6. Computer Vision
    7. Recommender Systems
    8. Time Series Analysis
    9. Ethics in AI
    10. Future Directions
    
    For each topic, include detailed explanations, mathematical formulas, 
    historical context, important papers, and real-world applications.
    Make this as comprehensive as possible - imagine you're writing a textbook.
    """
    
    # Create messages
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    
    # Add system message
    system = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant. When asked for comprehensive explanations, provide extremely detailed responses using your full context window."
        }
    ]
    
    # Test with standard output limit
    standard_limit = 4096
    logger.info(f"Making API call with standard limit: {standard_limit} tokens")
    
    try:
        # First test with standard limit to establish baseline
        start_time_standard = time.time()
        standard_response = client.messages.create(
            max_tokens=standard_limit,
            messages=messages,
            model="claude-3-7-sonnet-20250219",
            system=system
        )
        end_time_standard = time.time()
        standard_duration = end_time_standard - start_time_standard
        
        standard_text = standard_response.content[0].text
        standard_length = len(standard_text)
        logger.info(f"Standard response completed in {standard_duration:.2f} seconds")
        logger.info(f"Standard response length: {standard_length} characters")
        
        # Now test with extended output limit
        extended_limit = 128000  # 128K
        logger.info(f"Making API call with extended limit: {extended_limit} tokens")
        
        start_time_extended = time.time()
        extended_response = client.messages.create(
            max_tokens=extended_limit,
            messages=messages,
            model="claude-3-7-sonnet-20250219",
            system=system
        )
        end_time_extended = time.time()
        extended_duration = end_time_extended - start_time_extended
        
        extended_text = extended_response.content[0].text
        extended_length = len(extended_text)
        logger.info(f"Extended response completed in {extended_duration:.2f} seconds")
        logger.info(f"Extended response length: {extended_length} characters")
        
        # Compare results
        length_ratio = extended_length / standard_length if standard_length > 0 else 0
        logger.info(f"Length ratio (extended/standard): {length_ratio:.2f}x")
        
        # Save the extended output
        with open('extended_output.txt', 'w') as f:
            f.write(extended_text)
        
        # Save results summary
        with open('extended_output_results.txt', 'w') as f:
            f.write(f"EXTENDED OUTPUT TEST RESULTS\n")
            f.write(f"============================\n\n")
            f.write(f"Standard limit: {standard_limit} tokens\n")
            f.write(f"Extended limit: {extended_limit} tokens\n\n")
            f.write(f"Standard response:\n")
            f.write(f"- Time: {standard_duration:.2f} seconds\n")
            f.write(f"- Length: {standard_length} characters\n")
            f.write(f"- First 200 chars: {standard_text[:200]}...\n\n")
            f.write(f"Extended response:\n")
            f.write(f"- Time: {extended_duration:.2f} seconds\n")
            f.write(f"- Length: {extended_length} characters\n")
            f.write(f"- First 200 chars: {extended_text[:200]}...\n\n")
            f.write(f"Length ratio: {length_ratio:.2f}x\n")
            
            if length_ratio > 1.5:
                f.write(f"RESULT: Extended output successfully generated significantly more content.\n")
            else:
                f.write(f"RESULT: Extended output did not generate significantly more content.\n")
        
        # Return success if the extended output is significantly longer
        return length_ratio > 1.5
        
    except Exception as e:
        logger.error(f"Error in extended output test: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Extended Output Test (128K)")
    print("=" * 80)
    success = asyncio.run(test_extended_output())
    
    if success:
        print("\nTest completed successfully! Extended output capability confirmed.")
    else:
        print("\nTest failed or extended output not significantly longer. Check the logs for details.")