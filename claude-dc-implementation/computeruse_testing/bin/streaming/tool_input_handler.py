"""
Tool input handler for fixed_production_ready_loop.py
Ensures required parameters are provided for tools
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.tools')

def validate_tool_input(tool_name, tool_input):
    """
    Validate and potentially fix tool inputs
    Returns the validated (and possibly fixed) tool input
    """
    # Make a copy of the input to avoid modifying the original
    fixed_input = tool_input.copy() if tool_input else {}
    
    # Handle bash tool
    if tool_name.lower() == 'bash':
        if 'command' not in fixed_input or not fixed_input['command']:
            logger.warning("Bash tool called without a command, adding default diagnostic command")
            fixed_input['command'] = "echo 'Please specify a command to run with the bash tool'"
    
    # Handle computer tool
    elif tool_name.lower() == 'computer':
        if 'action' not in fixed_input or not fixed_input['action']:
            logger.warning("Computer tool called without an action, adding default action")
            fixed_input['action'] = "screenshot"
    
    # Log the tool input validation
    if fixed_input != tool_input:
        logger.info(f"Fixed input for {tool_name}: {fixed_input}")
    else:
        logger.info(f"Input for {tool_name} is valid: {fixed_input}")
    
    return fixed_input