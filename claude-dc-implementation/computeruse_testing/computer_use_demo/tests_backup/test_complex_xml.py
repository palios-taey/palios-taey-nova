#!/usr/bin/env python3
"""
Complex test for XML buffer implementation with challenging scenarios.

This test script creates complex scenarios for the XML buffer pattern to handle, including:
1. Partial XML that spans multiple delta events
2. XML with line breaks and whitespace
3. Deeply nested XML with multiple parameters
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_complex_xml")

# Set up Python path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "streaming"))

# Import streaming components
from streaming.unified_streaming_loop import unified_streaming_agent_loop
from streaming.dc_setup import dc_initialize

async def test_complex_xml_scenarios():
    """Test complex XML function calls with challenging scenarios."""
    logger.info("========== Testing Complex XML Function Call Scenarios ==========")
    
    # Load API key
    api_key = None
    
    # Try to load API key from secrets file
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                secrets = json.load(f)
                api_key = secrets["api_keys"]["anthropic"]
                logger.info(f"Loaded API key from {secrets_path}")
        except Exception as e:
            logger.warning(f"Error loading API key from {secrets_path}: {str(e)}")
    
    # Try alternate paths if needed
    if not api_key:
        for api_key_path in [
            Path("/home/computeruse/secrets/palios-taey-nova.json"),
            Path("/home/computeruse/secrets/palios-taey-secrets.json")
        ]:
            try:
                if api_key_path.exists():
                    with open(api_key_path, "r") as f:
                        secrets = json.load(f)
                        for key_name in ["api_key", "anthropic_api_key"]:
                            if key_name in secrets:
                                api_key = secrets[key_name]
                                break
                if api_key:
                    break
            except Exception as e:
                logger.warning(f"Error loading API key from {api_key_path}: {str(e)}")
    
    if not api_key:
        raise ValueError("API key not found in any secrets file")
    
    # Initialize DC
    dc_initialize(use_real_adapters=True)
    
    # Complex test prompts designed to challenge the buffer pattern
    test_prompts = [
        # Complex multiline command with quotes
        """Run a complex bash command:
        find all Python files in the current directory, count the lines in each, 
        and sort them by line count (most lines first).""",
        
        # Command with challenging structure
        """I need to see the first 5 lines and the last 5 lines of the unified_streaming_loop.py file, 
        can you do that for me? Also show the total line count.""",
        
        # Command with special characters
        """Create a new file called test_output.txt with the following content:
        <function_calls>
        <invoke name="example">
        <parameter name="test">value</parameter>
        </invoke>
        </function_calls>
        
        This should demonstrate that your buffer pattern works correctly."""
    ]
    
    # Test each prompt
    conversation_history = []
    for i, prompt in enumerate(test_prompts):
        logger.info(f"Test {i+1}: {prompt}")
        try:
            # Execute the agent loop
            conversation_history = await unified_streaming_agent_loop(
                user_input=prompt,
                conversation_history=conversation_history,
                api_key=api_key,
                model="claude-3-7-sonnet-20250219",
                max_tokens=4000,
                thinking_budget=None,  # Disable thinking to avoid API errors
                use_real_adapters=True
            )
            
            # Log success
            logger.info(f"Test {i+1} completed successfully")
            
            # Add separation between tests
            print("\n" + "="*50 + "\n")
        except Exception as e:
            # Log error
            logger.error(f"Test {i+1} failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("Complex XML function call tests completed.")

if __name__ == "__main__":
    asyncio.run(test_complex_xml_scenarios())