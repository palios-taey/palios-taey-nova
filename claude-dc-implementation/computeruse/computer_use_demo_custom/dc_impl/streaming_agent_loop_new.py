async def execute_tool_streaming(
    tool_name: str, 
    tool_input: Dict[str, Any],
    tool_id: str,
    on_progress: Optional[Callable[[str, float], None]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Execute a tool with progress updates during streaming.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        tool_id: The ID of the tool use in the conversation
        on_progress: Optional callback for progress updates
        
    Returns:
        Tuple of (tool_result, tool_result_content)
    """
    logger.info(f"Executing tool during streaming: {tool_name}")
    
    # Report initial progress
    if on_progress:
        await on_progress(f"Starting {tool_name} execution...", 0.0)
    
    try:
        # Check if we have a streaming implementation for this tool
        if tool_name == "dc_bash":
            try:
                # Try to import the streaming bash tool
                from tools.dc_bash import dc_execute_bash_tool_streaming, dc_process_streaming_output
                logger.info("Using streaming bash implementation")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_bash_tool_streaming(tool_input, on_progress):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    if "on_text" in callbacks:
                        callbacks["on_text"](chunk)
                
                # Process the collected output
                tool_result = await dc_process_streaming_output(
                    # Create a generator that yields the collected chunks
                    (chunk for chunk in output_chunks).__aiter__()
                )
                
                # Format the streaming result
                if tool_result.error:
                    tool_result_content = [{"type": "text", "text": tool_result.error}]
                else:
                    tool_result_content = [{"type": "text", "text": tool_result.output}]
                
                return tool_result, tool_result_content
            except ImportError:
                logger.warning("Streaming bash implementation not available, falling back to standard")
                
        elif tool_name == "dc_str_replace_editor":
            try:
                # Try to import the streaming file operations tool
                from tools.dc_file import dc_execute_file_tool_streaming, dc_process_streaming_output
                logger.info("Using streaming file operations implementation")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_file_tool_streaming(tool_input, on_progress):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    if "on_text" in callbacks:
                        callbacks["on_text"](chunk)
                
                # Process the collected output
                tool_result = await dc_process_streaming_output(
                    # Create a generator that yields the collected chunks
                    (chunk for chunk in output_chunks).__aiter__()
                )
                
                # Format the streaming result
                if tool_result.error:
                    tool_result_content = [{"type": "text", "text": tool_result.error}]
                else:
                    tool_result_content = [{"type": "text", "text": tool_result.output}]
                
                return tool_result, tool_result_content
            except ImportError:
                logger.warning("Streaming file operations implementation not available, falling back to standard")
        
        # Execute the tool with our namespace-isolated executor
        tool_result = await dc_execute_tool(
            tool_name=tool_name,
            tool_input=tool_input
        )
        
        # Report completion
        if on_progress:
            await on_progress(f"Completed {tool_name} execution", 1.0)
        
        # Format the tool result for the API
        tool_result_content = []
        if tool_result.error:
            # Add error content
            tool_result_content = [{
                "type": "text", 
                "text": tool_result.error
            }]
        else:
            # Add output content
            if tool_result.output:
                tool_result_content.append({
                    "type": "text",
                    "text": tool_result.output
                })
            
            # Add image content if available
            if tool_result.base64_image:
                tool_result_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": tool_result.base64_image
                    }
                })
        
        return tool_result, tool_result_content
    
    except Exception as e:
        logger.error(f"Error executing tool during streaming: {str(e)}")
        if on_progress:
            await on_progress(f"Error: {str(e)}", 1.0)
        
        # Return error result
        tool_result_content = [{
            "type": "text", 
            "text": f"Error executing tool: {str(e)}\n\n{traceback.format_exc()}"
        }]
        return None, tool_result_content