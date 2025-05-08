#!/usr/bin/env python3
"""
Direct test script for XML tool calls that uses direct imports to avoid package issues.
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_xml_test")

# Add streaming directory to path
streaming_dir = Path(__file__).parent / "streaming"
sys.path.insert(0, str(streaming_dir))

# Direct imports from streaming modules
from unified_streaming_loop import unified_streaming_agent_loop

def check_xml_validator():
    """Test that the XML validator works."""
    from xml_tool_validator import validate_xml_structure
    
    test_xml = """<function_calls>
<invoke name="dc_bash">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>"""
    
    is_valid, message, data = validate_xml_structure(test_xml)
    print(f"XML Validation Test: {'Passed' if is_valid else 'Failed'}")
    print(f"Message: {message}")
    print(f"Extracted data: {data}")
    
    return is_valid

async def test_xml_function_call():
    """Test the XML function call implementation."""
    
    # Load API key
    api_key = None
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            api_key = secrets.get("api_keys", {}).get("anthropic")
    
    if not api_key:
        print("API key not found. Using environment variable if available.")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("No API key available. Cannot proceed with test.")
        return
    
    test_prompt = "Run the 'ls -la' command and tell me what files are in the current directory. Use the XML function call format."
    
    print(f"\nTesting XML function calls with prompt: {test_prompt}")
    
    # Define callbacks
    def on_text(text):
        print(text, end="", flush=True)
    
    def on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        print(f"[Tool input: {json.dumps(tool_input, indent=2)}]", flush=True)
    
    def on_tool_result(tool_name, tool_input, tool_result):
        if hasattr(tool_result, "output") and tool_result.output:
            result = tool_result.output[:100] + "..." if len(tool_result.output) > 100 else tool_result.output
        else:
            result = "No output or error"
        print(f"\n[Tool result: {result}]", flush=True)
    
    def on_thinking(thinking):
        print(f"\n[Thinking: {thinking[:50]}...]", flush=True)
    
    def on_error(error, recoverable=False):
        print(f"\n[Error: {error}]", flush=True)
    
    # Run the test
    try:
        conversation_history = await unified_streaming_agent_loop(
            user_input=test_prompt,
            conversation_history=[],
            api_key=api_key,
            model="claude-3-5-sonnet-20240229",
            max_tokens=4000,
            thinking_budget=None,
            use_real_adapters=True,
            callbacks={
                "on_text": on_text,
                "on_thinking": on_thinking,
                "on_tool_use": on_tool_use,
                "on_tool_result": on_tool_result,
                "on_error": on_error
            }
        )
        
        print("\n\nTest completed successfully")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    # First check if XML validator works
    if check_xml_validator():
        # Then run the XML function call test
        asyncio.run(test_xml_function_call())
    else:
        print("XML validator test failed. Cannot proceed with XML function call test.")