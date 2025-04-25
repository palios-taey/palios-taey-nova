"""
Test script for production tools.
"""

import asyncio
from tools.computer import ComputerTool20250124
from tools.bash import BashTool20250124

async def test_prod_tools():
    """Test the production tools"""
    print("Production tool check:")
    
    # Check computer tool
    computer_tool = ComputerTool20250124()
    print(f"Computer tool type: {type(computer_tool)}")
    
    # Check bash tool
    bash_tool = BashTool20250124()
    print(f"Bash tool type: {type(bash_tool)}")
    
    # Test bash tool
    result = await bash_tool(command="echo Hello from Production")
    print(f"Bash result: {result.output}")
    
    print("Production test complete")

if __name__ == "__main__":
    asyncio.run(test_prod_tools())