#!/usr/bin/env python3
"""
Tools Fix Script
This script inspects the available tools and their formats to help debug integration issues.
"""

import os
import sys
import importlib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.tools_fix')

# Add necessary paths for imports
paths_to_add = [
    "/home/computeruse/computer_use_demo",
    "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Attempt to import from different possible locations
def import_tools():
    """Try importing tools from different locations."""
    try:
        # Try direct import
        import tools
        logger.info("Successfully imported tools directly")
        return tools
    except ImportError:
        try:
            # Try importing as a module
            tools = importlib.import_module("tools")
            logger.info("Successfully imported tools as module")
            return tools
        except ImportError:
            try:
                # Try computer_use_demo.tools
                tools = importlib.import_module("computer_use_demo.tools")
                logger.info("Successfully imported computer_use_demo.tools")
                return tools
            except ImportError as e:
                logger.error(f"Failed to import tools: {e}")
                return None

def main():
    """Inspect and fix tool issues."""
    print("=" * 80)
    print("Tools Inspection and Fix")
    print("=" * 80)
    
    # Import tools
    tools = import_tools()
    if not tools:
        print("Failed to import tools. Check the paths and try again.")
        return
    
    # Inspect tool groups
    if hasattr(tools, 'TOOL_GROUPS_BY_VERSION'):
        print("\nTool Groups by Version:")
        for version, group in tools.TOOL_GROUPS_BY_VERSION.items():
            print(f"- {version}: {group}")
            print(f"  Beta Flag: {getattr(group, 'beta_flag', 'None')}")
            print(f"  Tools: {[t.__name__ for t in getattr(group, 'tools', [])]}")
    
    # Create a tool collection and inspect it
    if hasattr(tools, 'ToolCollection'):
        print("\nTool Collection:")
        try:
            # Get computer_use_20250124 tool group if it exists
            tool_group = tools.TOOL_GROUPS_BY_VERSION.get("computer_use_20250124")
            if tool_group:
                tool_collection = tools.ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
                print(f"Created tool collection with {len(tool_collection.tools)} tools")
                
                # Print tools in collection
                print("\nTools in collection:")
                for tool in tool_collection.tools:
                    print(f"- {tool.name} (type: {getattr(tool, 'api_type', 'unknown')})")
                
                # Print tool parameters
                print("\nTool Parameters:")
                tool_params = tool_collection.to_params()
                for tool_param in tool_params:
                    print(f"- {tool_param}")
            else:
                print("computer_use_20250124 tool group not found")
        except Exception as e:
            print(f"Error creating tool collection: {e}")

if __name__ == "__main__":
    main()