# Streaming Implementation Plan

## Overview

This document outlines the plan for implementing streaming functionality with essential tools for Claude DC's self-bootstrapping approach. The goal is to ensure Claude DC can continue development while transitioning to streaming.

## Phase 1: Streaming Core Implementation (Current Phase)

### 1.1 Enhanced Streaming Agent Loop
- ✅ Create streaming agent loop with proper chunk processing
- ✅ Implement streaming session management
- ✅ Add tool state tracking during streaming
- ✅ Implement error handling and recovery

### 1.2 Essential Tools Integration (Next Steps)
- Create streaming-compatible bash tool implementation
- Implement file operations tool for streaming
- Update screenshot tool for streaming compatibility

### 1.3 Testing and Validation
- Create test suite for streaming implementation
- Test each essential tool individually
- Validate multi-turn interactions

## Phase 2: Advanced Streaming Features

### 2.1 Performance Optimization
- Implement better error recovery for interrupted streams
- Add performance metrics collection
- Optimize token usage during streaming

### 2.2 Enhanced Tool Support
- Add streaming support for mouse operations
- Implement keyboard input during streaming
- Create composite tool operations

### 2.3 User Experience Improvements
- Add progress bars for long-running operations
- Implement partial result rendering
- Create better error messages

## Implementation Timeline

### Week 1: Essential Tools Integration
- Day 1: Implement streaming bash tool
- Day 2: Create file operations tool for streaming
- Day 3: Update screenshot tool for streaming
- Day 4-5: Testing and debugging

### Week 2: Advanced Features
- Day 1-2: Implement performance optimizations
- Day 3-4: Add additional tool support
- Day 5: Documentation and final testing

## Implementation Details

### Streaming Bash Tool Enhancement

The current bash tool implementation needs to be updated to support streaming operations:

```python
async def dc_execute_bash_tool_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Execute a bash command with streaming output.
    
    Args:
        tool_input: The input parameters
        progress_callback: Optional callback for progress updates
        
    Yields:
        Command output chunks as they become available
    """
    command = tool_input.get("command", "")
    if not command:
        yield "Error: Empty command"
        return
        
    # Validate the command is read-only
    is_valid, message = dc_validate_read_only_command(command)
    if not is_valid:
        yield f"Error: {message}"
        return
        
    # Execute the command with streaming output
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Running: {command}", 0.0)
    
    # Stream stdout
    stdout_chunks = []
    async for line in process.stdout:
        line_str = line.decode('utf-8')
        stdout_chunks.append(line_str)
        yield line_str
        
        # Report progress (approximation)
        if progress_callback:
            await progress_callback(f"Running: {command}", 0.5)
    
    # Wait for completion
    await process.wait()
    
    # Get stderr if there was an error
    if process.returncode != 0:
        stderr = await process.stderr.read()
        stderr_str = stderr.decode('utf-8')
        yield f"Error (return code {process.returncode}): {stderr_str}"
    
    # Report completion
    if progress_callback:
        await progress_callback(f"Completed: {command}", 1.0)
```

### Streaming File Operations Tool

The file operations tool needs to be implemented for streaming:

```python
async def dc_execute_file_tool_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Execute a file operation with streaming output.
    
    Args:
        tool_input: The input parameters
        progress_callback: Optional callback for progress updates
        
    Yields:
        Operation output chunks as they become available
    """
    command = tool_input.get("command")
    path = tool_input.get("path")
    
    if not command:
        yield "Error: Missing required 'command' parameter"
        return
        
    if not path:
        yield "Error: Missing required 'path' parameter"
        return
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Starting {command} on {path}", 0.0)
    
    # Handle different commands
    if command == "view":
        try:
            # For large files, read line by line
            file_path = Path(path)
            if not file_path.exists():
                yield f"Error: File not found: {path}"
                return
                
            # Get file size for progress reporting
            file_size = file_path.stat().st_size
            bytes_read = 0
            
            with open(path, 'r') as f:
                yield f"Contents of {path}:\n"
                for i, line in enumerate(f):
                    yield f"{i+1}: {line}"
                    
                    # Update bytes read and report progress
                    bytes_read += len(line)
                    if progress_callback and file_size > 0:
                        progress = min(0.99, bytes_read / file_size)
                        await progress_callback(f"Reading {path}", progress)
        except Exception as e:
            yield f"Error reading file: {str(e)}"
    
    # Implement other commands as needed...
    
    # Report completion
    if progress_callback:
        await progress_callback(f"Completed {command} on {path}", 1.0)
```

### Test Implementation Examples

Example test for streaming bash command:

```python
async def test_streaming_bash_command():
    """Test streaming bash command execution."""
    # Initialize conversation
    conversation = []
    
    # Add user message
    user_input = "Run the command 'ls -la' to show files in the current directory"
    
    # Define callbacks to capture streaming output
    output_chunks = []
    
    def on_text(text):
        output_chunks.append(text)
    
    # Run streaming agent loop
    conversation = await dc_streaming_agent_loop(
        user_input=user_input,
        conversation_history=conversation,
        callbacks={"on_text": on_text},
        use_real_adapters=True
    )
    
    # Validate results
    assert len(output_chunks) > 0, "Should have received streaming output"
    assert any("ls -la" in chunk for chunk in output_chunks), "Should contain bash command"
```

## Success Criteria

The implementation will be considered successful when:

1. Claude DC can use streaming to:
   - Execute bash commands and see results in real-time
   - View and modify files with streaming support
   - Take screenshots and process them during streaming

2. The system provides:
   - Reliable error handling and recovery
   - Progress updates during long-running operations
   - Multi-turn interactions during streaming

3. All essential tools work seamlessly with streaming, enabling continued development.