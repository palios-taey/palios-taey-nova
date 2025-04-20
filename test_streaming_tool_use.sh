#!/bin/bash
# Simple test script for streaming and tool use in Claude DC
# This script should be run inside the container

set -e  # Exit on error

echo "==================================================="
echo "  Claude DC Streaming + Tool Use Test"
echo "==================================================="

# Check if we're inside the container
if [ ! -d "/home/computeruse" ]; then
  echo "❌ This script must be run inside the Computer Use container."
  echo "First, launch the container with:"
  echo "  ./current-execution-status/claude-integration/launch_computer_use.sh"
  echo "Then, inside the container:"
  echo "  cd github/palios-taey-nova && ./test_streaming_tool_use.sh"
  exit 1
fi

# Set essential environment variables
export WIDTH=1024
export HEIGHT=768
export DISPLAY_NUM=1
export DISPLAY=:1
export ENABLE_STREAMING=true
export ENABLE_THINKING=true
export ENABLE_PROMPT_CACHING=false
export ENABLE_EXTENDED_OUTPUT=false
export ENABLE_TOKEN_EFFICIENT=false

echo "✅ Environment configured for simple streaming test"
echo "- Streaming: ENABLED"
echo "- Thinking: ENABLED"
echo "- Beta features: ALL DISABLED"

# Create a Python test script
TEMP_SCRIPT="/home/computeruse/test_streaming.py"
cat > $TEMP_SCRIPT << 'EOF'
#!/usr/bin/env python3
"""
Simplified test script to verify streaming with tool use
"""
import os
import sys
import asyncio
from pathlib import Path

# Set up Python path
repo_root = Path("/home/computeruse/github/palios-taey-nova")
claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo = claude_dc_root / "computeruse/computer_use_demo"

# Add paths to Python path
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(claude_dc_root))
sys.path.insert(0, str(claude_dc_root / "computeruse"))

# Import required modules
from computer_use_demo import (
    ENABLE_STREAMING,
    ENABLE_THINKING,
    ENABLE_PROMPT_CACHING,
    ENABLE_EXTENDED_OUTPUT
)

from computer_use_demo.loop import sampling_loop
from computer_use_demo.tools import ToolResult
from anthropic import APIError, Anthropic
from anthropic.types.beta import BetaContentBlockParam, BetaMessageParam

print("\nRunning streaming test with tool use...")
print(f"Streaming: {'enabled' if ENABLE_STREAMING else 'disabled'}")
print(f"Thinking: {'enabled' if ENABLE_THINKING else 'disabled'}")
print(f"Prompt caching: {'enabled' if ENABLE_PROMPT_CACHING else 'disabled'}")
print(f"Extended output: {'enabled' if ENABLE_EXTENDED_OUTPUT else 'disabled'}")

async def run_test():
    """Simple test of streaming responses with tool use"""
    
    # A simple output callback to show streamed output
    def output_callback(content: BetaContentBlockParam):
        if isinstance(content, dict):
            if content.get("type") == "text":
                print(f"Text: {content.get('text', '')}")
            elif content.get("type") == "thinking":
                print(f"Thinking: {content.get('thinking', '')}")
            elif content.get("type") == "tool_use":
                print(f"Tool use: {content.get('name', '')} - {content.get('input', {})}")
    
    # A simple tool output callback
    def tool_output_callback(result: ToolResult, tool_id: str):
        print(f"Tool result for {tool_id}: {result.output}")
    
    # API response callback
    def api_response_callback(request, response, error):
        if error:
            print(f"API ERROR: {error}")
    
    # Simple test messages
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! Please use a tool to get the current date and time."
                }
            ]
        }
    ]
    
    try:
        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            api_key_path = Path.home() / ".anthropic" / "api_key"
            if api_key_path.exists():
                api_key = api_key_path.read_text().strip()
            else:
                print("ERROR: No API key found!")
                return
        
        # Run the agent loop
        print("\nStarting agent loop with streaming...")
        await sampling_loop(
            model="claude-3-7-sonnet-20250219",
            provider="anthropic",
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=api_key,
            max_tokens=4096,  # Small limit for test
            thinking_budget=2048 if ENABLE_THINKING else None,
        )
        
        print("\nTest completed successfully!")
    
    except APIError as e:
        print(f"Anthropic API Error: {e}")
    except Exception as e:
        print(f"Error in test: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
EOF

chmod +x $TEMP_SCRIPT

echo
echo "Running the streaming test..."
echo "----------------------------"
echo

python3 $TEMP_SCRIPT

echo
echo "Test complete!"
echo "Check the output above to verify that streaming and tool use are working properly."
echo "If you see incremental text output and tool usage, the test passed."
echo