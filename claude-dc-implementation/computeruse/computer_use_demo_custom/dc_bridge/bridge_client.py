"""
Bridge client for connecting the enhanced bridge to production tools.
Provides a simple interface for production code to access the enhanced implementation.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bridge_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bridge_client")

# Import the enhanced bridge
from dc_bridge.enhanced_bridge import (
    execute_tool,
    get_metrics,
    get_feature_toggles,
    set_feature_toggle,
    clear_cache
)

class BridgeClient:
    """Client for the enhanced bridge."""
    
    def __init__(self, use_real_tools: bool = False):
        """Initialize the bridge client."""
        self.use_real_tools = use_real_tools
        self.initialized = False
    
    async def initialize(self):
        """Initialize the bridge client."""
        if not self.initialized:
            await self._async_initialize()
            self.initialized = True
    
    async def _async_initialize(self):
        """Async initialization."""
        # Set feature toggles based on configuration
        await set_feature_toggle("use_real_tools", self.use_real_tools)
        logger.info(f"Bridge client initialized with use_real_tools={self.use_real_tools}")
    
    async def execute_computer_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a computer action."""
        tool_input = {"action": action, **kwargs}
        logger.info(f"Executing computer action: {action} with kwargs: {kwargs}")
        result = await execute_tool("dc_computer", tool_input)
        return result
    
    async def execute_bash_command(self, command: str) -> Dict[str, Any]:
        """Execute a bash command."""
        logger.info(f"Executing bash command: {command}")
        result = await execute_tool("dc_bash", {"command": command})
        return result
    
    async def get_bridge_metrics(self) -> Dict[str, Any]:
        """Get metrics from the bridge."""
        logger.info("Getting bridge metrics")
        metrics = await get_metrics()
        return metrics
    
    async def get_bridge_toggles(self) -> Dict[str, bool]:
        """Get feature toggles from the bridge."""
        logger.info("Getting bridge toggles")
        toggles = await get_feature_toggles()
        return toggles
    
    async def set_bridge_toggle(self, feature: str, enabled: bool) -> Dict[str, Any]:
        """Set a feature toggle."""
        logger.info(f"Setting bridge toggle {feature} to {enabled}")
        result = await set_feature_toggle(feature, enabled)
        return result
    
    async def clear_bridge_cache(self) -> Dict[str, Any]:
        """Clear the bridge cache."""
        logger.info("Clearing bridge cache")
        result = await clear_cache()
        return result

# Singleton instance
_client = None

def get_client(use_real_tools: bool = False) -> BridgeClient:
    """Get the bridge client singleton."""
    global _client
    if _client is None:
        _client = BridgeClient(use_real_tools=use_real_tools)
    return _client

# Convenience functions
async def execute_computer_action(action: str, **kwargs) -> Dict[str, Any]:
    """Execute a computer action."""
    client = get_client()
    await client.initialize()
    return await client.execute_computer_action(action, **kwargs)

async def execute_bash_command(command: str) -> Dict[str, Any]:
    """Execute a bash command."""
    client = get_client()
    await client.initialize()
    return await client.execute_bash_command(command)

async def get_bridge_metrics() -> Dict[str, Any]:
    """Get metrics from the bridge."""
    client = get_client()
    await client.initialize()
    return await client.get_bridge_metrics()

async def get_bridge_toggles() -> Dict[str, bool]:
    """Get feature toggles from the bridge."""
    client = get_client()
    await client.initialize()
    return await client.get_bridge_toggles()

async def set_bridge_toggle(feature: str, enabled: bool) -> Dict[str, Any]:
    """Set a feature toggle."""
    client = get_client()
    await client.initialize()
    return await client.set_bridge_toggle(feature, enabled)

async def clear_bridge_cache() -> Dict[str, Any]:
    """Clear the bridge cache."""
    client = get_client()
    await client.initialize()
    return await client.clear_bridge_cache()