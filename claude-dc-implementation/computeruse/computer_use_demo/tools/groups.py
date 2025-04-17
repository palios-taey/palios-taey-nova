from .bash import BashTool20250124, BashTool20241022
from .computer import ComputerTool20250124, ComputerTool20241022
#from .edit import EditTool20250124, EditTool20241022  # if an Edit tool existed

class ToolCollection:
    """A collection of Anthropic tools, for registration and lookup."""
    def __init__(self, *tools):
        self.tools = list(tools)

    def to_params(self):
        # Returns a list of tool definitions (type & name) for API registration
        return [tool.to_params() for tool in self.tools]

    def get_tool(self, name: str):
        # Retrieve a tool instance by name
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

# Register tool sets for each supported version
TOOLS_20241022 = ToolCollection(
    BashTool20241022(),
    ComputerTool20241022(),
    # EditTool20241022()  # if edit tool existed
)

TOOLS_20250124 = ToolCollection(
    BashTool20250124(),
    ComputerTool20250124(),
    # EditTool20250124()  # if edit tool existed
)

# If only 20250124 is supported, we can choose it as the default
DEFAULT_TOOLS = TOOLS_20250124

