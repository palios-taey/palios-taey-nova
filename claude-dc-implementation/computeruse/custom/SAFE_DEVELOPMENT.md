# Safe Development Guidelines for Claude DC

## Environment Isolation Principles

When developing or testing new features, follow these guidelines to maintain a stable production environment:

### 1. Development/Testing Directory Structure

Always use this directory structure for all development work:
```
/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom/
```

Key subdirectories:
- `dev/` - For active development
- `testing/` - For integration testing
- `experiments/` - For experimental features
- `adapters/` - For integration with production tools

### 2. Never Modify Production Directly

DO NOT modify or create files in:
- `/home/computeruse/` and its subdirectories
- Any path outside the designated development directories

### 3. Testing Methodology

When testing new implementations:

1. **Create isolated test files**:
   ```python
   # Example test file structure
   /claude-dc-implementation/computeruse/custom/testing/test_tool_adapters.py
   ```

2. **Use explicit imports**:
   ```python
   # Always use absolute imports from the development directory
   from claude_dc_implementation.computeruse.custom.adapters import MyAdapter
   ```

3. **Mock production dependencies**:
   ```python
   # Example of mocking production tools
   class MockComputerTool:
       async def screenshot(self, **kwargs):
           return {"success": True, "base64_image": "test_image_data"}
   ```

### 4. Integration Process

When ready to integrate with production:

1. **Create a backup**:
   ```bash
   # Example backup command (run in your development environment)
   cp -r /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom_backup_YYYYMMDD
   ```

2. **Document the changes**:
   ```markdown
   # Change documentation in CHANGES.md
   ## Integration YYYY-MM-DD
   - Added feature X
   - Modified component Y
   - Testing coverage: 95%
   ```

3. **Perform controlled integration**:
   - Start with the lowest-risk components
   - Test each component immediately after integration
   - Have rollback plan ready

### 5. Recommended Testing Pattern

For all new development:

```python
# 1. Create test file
# /claude-dc-implementation/computeruse/custom/testing/test_feature.py

import unittest
from unittest.mock import patch, MagicMock

# 2. Import the feature to test
from claude_dc_implementation.computeruse.custom.my_module import MyFeature

# 3. Create test class
class TestMyFeature(unittest.TestCase):
    def setUp(self):
        # Set up isolated test environment
        self.test_dir = "/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom/testing/test_data"
        # Create necessary test data/files
        
    def test_feature_functionality(self):
        # Test the feature in isolation
        
    def tearDown(self):
        # Clean up any test artifacts
```

### 6. Safe File Operations

When working with files:

1. **Always use Path from pathlib**:
   ```python
   from pathlib import Path
   
   # Define base development directory
   DEV_DIR = Path("/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom")
   
   # Create paths safely within development directory
   test_file = DEV_DIR / "testing" / "test_data" / "sample.txt"
   ```

2. **Validate paths before operations**:
   ```python
   def safe_write(filepath, content):
       """Safely write to a file, ensuring it's within allowed directories."""
       path = Path(filepath).resolve()
       if not str(path).startswith(str(DEV_DIR)):
           raise ValueError(f"Cannot write to path outside dev directory: {path}")
       # Proceed with write operation
   ```

### 7. Running Tests Safely

Execute tests with proper isolation:

```bash
# Run from development directory
cd /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom

# Run specific test
python -m unittest testing.test_feature

# Run all tests
python -m unittest discover testing
```

## Example: Safe Tool Integration

```python
# /claude-dc-implementation/computeruse/custom/adapters/tool_adapter.py

from pathlib import Path
import sys
import logging

# Set up logging to development directory
log_dir = Path("/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom/logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / "tool_adapter.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define adapter that integrates with production tools
class ToolAdapter:
    def __init__(self):
        self.logger = logging.getLogger("tool_adapter")
        
    async def execute_tool(self, tool_name, tool_input):
        """Safely execute a tool by adapting to production interface."""
        self.logger.info(f"Executing {tool_name} with input: {tool_input}")
        
        try:
            # Safe implementation that doesn't directly modify production
            # ...implementation details...
            
            return {"success": True, "result": "Tool executed safely"}
        except Exception as e:
            self.logger.error(f"Tool execution failed: {str(e)}")
            return {"success": False, "error": str(e)}
```

By following these guidelines, you'll maintain the integrity of your production environment while enabling efficient development and testing.