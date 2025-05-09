"""
Test script for streaming implementation.
Tests the streaming capabilities of the Claude DC implementation.
"""
import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_streaming")

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    logger.error("nest_asyncio not installed. Install with: pip install nest_asyncio")
    sys.exit(1)

try:
    from anthropic import AsyncAnthropic
    import anthropic
    logger.info(f"Using Anthropic SDK version: {anthropic.__version__}")
except ImportError:
    logger.error("Anthropic SDK not installed. Install with: pip install anthropic==0.50.0")
    sys.exit(1)

# Import agent loop
try:
    from loop import agent_loop, AVAILABLE_TOOLS
    logger.info("Successfully imported agent_loop")
except ImportError as e:
    logger.error(f"Failed to import agent_loop: {e}")
    sys.exit(1)

async def test_basic_streaming():
    """Test basic text streaming without tools"""
    logger.info("Testing basic text streaming...")
    
    # Create client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return False
        
    client = AsyncAnthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
    )
    
    # Track received events
    events_received = []
    content_received = ""
    
    async def event_handler(event):
        events_received.append(event.type)
        nonlocal content_received
        if event.type == "content_block_delta" and event.delta.type == "text_delta":
            content_received += event.delta.text
    
    # Run test with simple prompt
    messages = [{"role": "user", "content": "Say hello in one sentence"}]
    
    try:
        response = await agent_loop(
            client=client,
            messages=messages,
            max_tokens=100,
            stream_handler=event_handler
        )
        
        # Check for essential event types
        required_events = ["message_start", "content_block_start", "content_block_delta", "content_block_stop", "message_stop"]
        missing_events = [event for event in required_events if event not in events_received]
        
        if missing_events:
            logger.error(f"Missing required event types: {missing_events}")
            return False
            
        # Check content
        if not content_received:
            logger.error("No content received from streaming")
            return False
            
        logger.info(f"Content received: {content_received}")
        logger.info(f"Event types received: {set(events_received)}")
        logger.info("Basic streaming test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error in basic streaming test: {e}")
        return False

async def test_thinking_parameter():
    """Test thinking parameter functionality"""
    logger.info("Testing thinking parameter...")
    
    # Create client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return False
        
    client = AsyncAnthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
    )
    
    # Run with thinking enabled
    messages = [{"role": "user", "content": "What is 123 * 456? Show your work."}]
    thinking = {"type": "enabled", "budget_tokens": 512}
    
    try:
        response = await agent_loop(
            client=client,
            messages=messages,
            max_tokens=200,
            thinking=thinking
        )
        
        # Verify thinking was included
        if not response or not response.get("thinking"):
            logger.error("Thinking parameter test failed - no thinking in response")
            return False
            
        logger.info(f"Thinking received: {response['thinking'][:100]}...")
        logger.info("Thinking parameter test passed!")
        return True
            
    except Exception as e:
        logger.error(f"Error in thinking parameter test: {e}")
        return False

async def test_tool_streaming():
    """Test streaming with tool use"""
    logger.info("Testing streaming with tool use...")
    
    # Create client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return False
        
    client = AsyncAnthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
    )
    
    # Track events
    events_received = []
    tool_use_detected = False
    
    async def event_handler(event):
        events_received.append(event.type)
        nonlocal tool_use_detected
        
        if event.type == "content_block_start" and event.content_block.type == "tool_use":
            tool_use_detected = True
            logger.info("Tool use block detected!")
            
        if event.type == "content_block_delta" and getattr(event.delta, "type", None) == "input_json_delta":
            logger.info(f"Tool input delta: {event.delta.partial_json}")
    
    # Run test with tool-triggering prompt
    messages = [{"role": "user", "content": "Show me the current date and time by running a bash command"}]
    
    try:
        response = await agent_loop(
            client=client,
            messages=messages,
            max_tokens=1000,
            stream_handler=event_handler,
            tools=AVAILABLE_TOOLS
        )
        
        # Check for tool use
        if not tool_use_detected:
            logger.error("No tool use detected in streaming")
            return False
            
        # Check tool execution results
        if not response or not response.get("tool_use"):
            logger.error("No tool execution results in response")
            return False
            
        logger.info(f"Tool use in response: {response['tool_use']}")
        logger.info("Tool streaming test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error in tool streaming test: {e}")
        return False

async def run_all_tests():
    """Run all streaming tests"""
    results = {}
    
    results["basic_streaming"] = await test_basic_streaming()
    results["thinking_parameter"] = await test_thinking_parameter()
    results["tool_streaming"] = await test_tool_streaming()
    
    # Print summary
    print("\n" + "=" * 60)
    print(" Streaming Tests Results ".center(60, "="))
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.ljust(20)}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    print(f" Overall: {'✅ PASSED' if all_passed else '❌ FAILED'} ".center(60, "="))
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)