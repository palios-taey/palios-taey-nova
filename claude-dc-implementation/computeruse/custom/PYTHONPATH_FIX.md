# Python Path Isolation Guide

## Critical Issue: Import Path Conflicts

We've discovered that modules created in the development directory are affecting the production environment due to Python's import system.

## Root Cause

When Python modules with similar names or package structures to production are created in development directories, they can be discovered through:
- `PYTHONPATH` environment variable
- Relative imports
- `sys.path` modifications

## Solution: Module Namespacing

### 1. Use Unique Namespace

Always prefix your module names with a unique identifier that won't conflict with production:

```
# Instead of this:
/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/adapters/

# Use this:
/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_custom_adapters/
```

### 2. Explicit Package Structure

Create a complete package structure with clear namespacing:

```python
# Directory structure
/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/
    __init__.py
    tools/
        __init__.py
        adapters.py
    registry/
        __init__.py
        tool_registry.py
```

### 3. Explicit Imports

Always use fully qualified imports:

```python
# Good
from claude_dc_implementation.computeruse.custom.dc_impl.tools import adapters

# Avoid
from tools import adapters  # Ambiguous and could conflict
```

## Testing Without Conflicts

When running tests:

```bash
# Set a clean PYTHONPATH for testing
cd /home/computeruse/github/palios-taey-nova/
PYTHONPATH=$(pwd) python -m claude_dc_implementation.computeruse.custom.dc_impl.tests.test_tools
```

## Practical Example

```python
# File: /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/__init__.py
"""
Custom Claude DC implementation with isolated namespace.
"""

# File: /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/tools/adapters.py
"""
Tool adapters with namespace isolation.
"""
from typing import Dict, Any

class DCToolAdapter:
    """Adapter class with distinctive name to avoid conflicts."""
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]):
        """Execute a tool with proper isolation."""
        # Implementation...
```

## Key Safety Measures

1. **Never use common module names** like:
   - `tools`
   - `models`
   - `adapters`
   - `utils`

2. **Always use distinctive class/function names** with prefixes:
   - `DCToolAdapter` instead of `ToolAdapter`
   - `dc_execute_tool` instead of `execute_tool`

3. **Check for conflicts before development**:
   ```bash
   # Find potential naming conflicts
   find /home/computeruse -name "*.py" -exec grep -l "class ToolAdapter" {} \;
   ```

By following these guidelines, you can develop safely without impacting the production environment.