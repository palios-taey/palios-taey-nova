#!/usr/bin/env python3

import asyncio
from bash_streaming import dc_execute_bash_tool
from streaming_adapters import streaming_adapter

async def main():
    print("\n=== Testing Bash Tool ===")
    # Test the bash tool with a simple command
    result = await dc_execute_bash_tool({"command": "echo 'Hello streaming!'"})
    print("Output:", result.output)
    print("Error:", result.error)
    
    # Test with an invalid command
    result = await dc_execute_bash_tool({"command": "invalid_command"})
    print("Invalid command error:", result.error)
    
    print("\n=== Testing Streaming Adapter ===")
    # Test the streaming adapter
    chunks = []
    async def collect_chunks():
        async for chunk in streaming_adapter.execute_tool_streaming(
            tool_name="dc_bash",
            tool_input={"command": "echo 'Hello from adapter!'"},
            tool_id="test_1",
            on_progress=async_progress_callback
        ):
            chunks.append(chunk)
            print("Chunk:", chunk.strip())
    
    async def async_progress_callback(message, progress):
        print(f"Progress: {message} - {progress:.0%}")
    
    await collect_chunks()
    print("\nCombined output:", "".join(chunks))
    print("\nActive tools:", streaming_adapter.get_active_tools())

if __name__ == "__main__":
    asyncio.run(main())