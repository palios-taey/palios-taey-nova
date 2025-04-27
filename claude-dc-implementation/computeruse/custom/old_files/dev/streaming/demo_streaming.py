#!/usr/bin/env python3
"""
Demo script for Claude DC streaming implementation.

This script demonstrates the streaming functionality of the bash tool
and adapter framework.
"""

import asyncio
import sys
from pathlib import Path

# Import streaming components
from bash_streaming import dc_execute_bash_tool_streaming
from streaming_adapters import execute_streaming_bash, streaming_adapter

async def demo_direct_bash():
    """Demonstrate direct bash streaming."""
    print("\n===== Direct Bash Streaming Demo =====\n")
    
    # Define progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Execute command with streaming
    command = "ls -la /home"
    print(f"Executing command: {command}")
    print("-" * 40)
    
    async for chunk in dc_execute_bash_tool_streaming(
        {"command": command},
        progress_callback=progress_callback
    ):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 40)

async def demo_adapter_bash():
    """Demonstrate bash streaming through adapter."""
    print("\n===== Adapter Bash Streaming Demo =====\n")
    
    # Define progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Execute command with adapter
    command = "cat /etc/hostname"
    print(f"Executing command: {command}")
    print("-" * 40)
    
    async for chunk in execute_streaming_bash(command, progress_callback):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 40)
    
    # Show active tools
    print("\nActive tools:")
    for tool_id, tool_info in streaming_adapter.get_active_tools().items():
        print(f"- {tool_id}: {tool_info}")

async def demo_multiple_commands():
    """Demonstrate executing multiple commands in sequence."""
    print("\n===== Multiple Commands Demo =====\n")
    
    # Define progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Commands to execute
    commands = [
        "echo 'Hello from streaming!'",
        "date",
        "uname -a",
        "ls -la /home/computeruse/github",
    ]
    
    # Execute each command
    for i, command in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] Executing: {command}")
        print("-" * 40)
        
        async for chunk in execute_streaming_bash(command, progress_callback):
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 40)
        
        # Wait a bit between commands
        await asyncio.sleep(0.5)

async def demo_long_running_command():
    """Demonstrate streaming output for a long-running command."""
    print("\n===== Long Running Command Demo =====\n")
    
    # Define progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Use find command which can take time
    command = "find /home/computeruse -name '*.py' | sort"
    print(f"Executing long-running command: {command}")
    print("-" * 40)
    
    line_count = 0
    async for chunk in execute_streaming_bash(command, progress_callback):
        print(chunk, end="", flush=True)
        line_count += chunk.count('\n')
    
    print("\n" + "-" * 40)
    print(f"Received {line_count} lines of output")

async def demo_interactive():
    """Interactive demo allowing user to enter commands."""
    print("\n===== Interactive Streaming Demo =====\n")
    print("Enter bash commands to execute with streaming (type 'exit' to quit)")
    
    # Define progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    while True:
        # Get user input
        command = input("\nCommand> ")
        
        # Check for exit command
        if command.lower() in ['exit', 'quit', 'q']:
            break
        
        # Skip empty commands
        if not command.strip():
            continue
        
        print("-" * 40)
        
        # Execute the command
        try:
            async for chunk in execute_streaming_bash(command, progress_callback):
                print(chunk, end="", flush=True)
            
            print("\n" + "-" * 40)
        except Exception as e:
            print(f"\nError: {str(e)}")

async def main():
    """Main demo function."""
    print("\nClaude DC Streaming Implementation Demo")
    print("======================================\n")
    
    # Show available demos
    demos = {
        "1": ("Direct bash streaming", demo_direct_bash),
        "2": ("Adapter bash streaming", demo_adapter_bash),
        "3": ("Multiple commands", demo_multiple_commands),
        "4": ("Long-running command", demo_long_running_command),
        "5": ("Interactive mode", demo_interactive),
        "a": ("Run all demos", None),
    }
    
    print("Available demos:")
    for key, (name, _) in demos.items():
        print(f"{key}: {name}")
    
    # Get user choice
    choice = input("\nSelect a demo (or 'a' for all): ")
    
    if choice == "a":
        # Run all demos except interactive
        for key, (_, demo_func) in demos.items():
            if key != "5" and demo_func:  # Skip interactive mode in "all"
                await demo_func()
    elif choice in demos:
        # Run selected demo
        _, demo_func = demos[choice]
        if demo_func:
            await demo_func()
    else:
        print(f"Invalid choice: {choice}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("\nDemo completed successfully!")
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")