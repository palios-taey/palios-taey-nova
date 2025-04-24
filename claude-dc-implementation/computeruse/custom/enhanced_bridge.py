"""
Enhanced bridge module for DC Custom Implementation.
Provides metrics collection, caching, and improved diagnostics.
"""

import sys
import time
import logging
import asyncio
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dc_bridge_enhanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dc_bridge_enhanced")

# Add GitHub directory to path
GITHUB_DIR = Path("/home/computeruse/github/palios-taey-nova")
if str(GITHUB_DIR) not in sys.path:
    sys.path.insert(0, str(GITHUB_DIR))
    logger.info(f"Added {GITHUB_DIR} to sys.path")

# Metrics collection
class BridgeMetrics:
    """Collects metrics for bridge operations"""
    def __init__(self, max_history: int = 100):
        self.calls = 0
        self.errors = 0
        self.call_times: Dict[str, List[float]] = defaultdict(list)
        self.error_history: deque = deque(maxlen=max_history)
        self.recent_calls: deque = deque(maxlen=max_history)
        self.start_time = datetime.now()
    
    def record_call(self, tool_name: str, tool_input: Dict[str, Any], duration: float, success: bool) -> None:
        """Record a tool call"""
        self.calls += 1
        self.call_times[tool_name].append(duration)
        
        if not success:
            self.errors += 1
        
        self.recent_calls.append({
            "timestamp": datetime.now(),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "duration": duration,
            "success": success
        })
    
    def record_error(self, tool_name: str, tool_input: Dict[str, Any], error: str) -> None:
        """Record an error"""
        self.errors += 1
        self.error_history.append({
            "timestamp": datetime.now(),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "error": error,
            "traceback": traceback.format_exc()
        })
    
    def get_avg_time(self, tool_name: Optional[str] = None) -> float:
        """Get average execution time for a tool or all tools"""
        if tool_name:
            times = self.call_times.get(tool_name, [])
            return sum(times) / len(times) if times else 0
        
        all_times = [t for times in self.call_times.values() for t in times]
        return sum(all_times) / len(all_times) if all_times else 0
    
    def get_success_rate(self) -> float:
        """Get the success rate for all calls"""
        if not self.calls:
            return 1.0
        return (self.calls - self.errors) / self.calls
    
    def get_report(self) -> Dict[str, Any]:
        """Get a complete metrics report"""
        tool_stats = {}
        for tool_name, times in self.call_times.items():
            tool_stats[tool_name] = {
                "calls": len(times),
                "avg_time": sum(times) / len(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0
            }
        
        return {
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "total_calls": self.calls,
            "total_errors": self.errors,
            "success_rate": self.get_success_rate(),
            "overall_avg_time": self.get_avg_time(),
            "tool_stats": tool_stats,
            "recent_errors": list(self.error_history),
            "recent_calls": list(self.recent_calls)
        }

# Create metrics collector
metrics = BridgeMetrics()

# Simple cache for tool results
class ResultCache:
    """Caches tool results to improve performance"""
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl  # Time-to-live in seconds
    
    def _get_key(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Create a cache key from tool name and input"""
        input_str = str(sorted(tool_input.items()))
        return f"{tool_name}:{input_str}"
    
    def get(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[Any]:
        """Get a cached result if it exists and is not expired"""
        key = self._get_key(tool_name, tool_input)
        if key in self.cache:
            timestamp, result = self.cache[key]
            if time.time() - timestamp <= self.ttl:
                return result
            # Remove expired entry
            del self.cache[key]
        return None
    
    def set(self, tool_name: str, tool_input: Dict[str, Any], result: Any) -> None:
        """Cache a tool result"""
        # Ensure cache doesn't exceed max size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.items(), key=lambda x: x[1][0])[0]
            del self.cache[oldest_key]
        
        key = self._get_key(tool_name, tool_input)
        self.cache[key] = (time.time(), result)

# Create result cache
cache = ResultCache()

# Feature toggle system
class FeatureToggles:
    """Manages feature toggles for the bridge"""
    def __init__(self):
        self.toggles = {
            "use_custom_implementation": True,
            "use_caching": True,
            "collect_metrics": True,
            "use_real_tools": True,
            "use_fallbacks": True
        }
        
        # Load toggles from config file if available
        config_path = Path("dc_bridge_config.txt")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            key, value = line.split("=")
                            self.toggles[key.strip()] = value.strip().lower() == "true"
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.toggles.get(feature, False)
    
    def set_feature(self, feature: str, enabled: bool) -> None:
        """Set a feature toggle"""
        self.toggles[feature] = enabled
        
        # Save to config file
        try:
            with open("dc_bridge_config.txt", "w") as f:
                for key, value in self.toggles.items():
                    f.write(f"{key}={str(value).lower()}\n")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")

# Create feature toggles
toggles = FeatureToggles()

# Import from custom implementation
try:
    from claude_dc_implementation.computeruse.custom.dc_impl.dc_setup import dc_initialize
    from claude_dc_implementation.computeruse.custom.dc_impl.dc_executor import dc_execute_tool
    
    # Initialize the implementation
    dc_initialize()
    logger.info("Successfully imported and initialized DC Custom Implementation")
    DC_CUSTOM_AVAILABLE = True
except Exception as e:
    logger.error(f"Error importing DC Custom Implementation: {str(e)}")
    DC_CUSTOM_AVAILABLE = False

async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool using the custom implementation.
    Includes metrics collection, caching, and fallback capabilities.
    """
    start_time = time.time()
    success = False
    
    try:
        # Check if custom implementation should be used
        if not toggles.is_enabled("use_custom_implementation"):
            logger.info("Custom implementation disabled by feature toggle")
            result = {"output": f"Mock execution of {tool_name} with input {tool_input} (toggle disabled)"}
            metrics.record_call(tool_name, tool_input, time.time() - start_time, True)
            return result
        
        # Check cache if enabled
        if toggles.is_enabled("use_caching"):
            cached_result = cache.get(tool_name, tool_input)
            if cached_result:
                logger.info(f"Cache hit for {tool_name}")
                metrics.record_call(tool_name, tool_input, time.time() - start_time, True)
                return cached_result
        
        # Use custom implementation if available
        if DC_CUSTOM_AVAILABLE and toggles.is_enabled("use_real_tools"):
            try:
                # Execute the tool using the custom implementation
                custom_result = await dc_execute_tool(tool_name, tool_input)
                
                # Convert to the format expected by production
                result = {
                    "output": custom_result.output,
                    "error": custom_result.error,
                    "base64_image": custom_result.base64_image
                }
                
                success = not custom_result.error
                
                # Cache the result if caching is enabled
                if toggles.is_enabled("use_caching") and success:
                    cache.set(tool_name, tool_input, result)
                
                # Record metrics
                if toggles.is_enabled("collect_metrics"):
                    metrics.record_call(tool_name, tool_input, time.time() - start_time, success)
                
                return result
            except Exception as e:
                logger.error(f"Error executing tool with custom implementation: {str(e)}")
                
                # Record error metrics
                if toggles.is_enabled("collect_metrics"):
                    metrics.record_error(tool_name, tool_input, str(e))
                
                # Fall back to mock implementation if fallbacks are enabled
                if not toggles.is_enabled("use_fallbacks"):
                    raise
        
        # Fall back to mock implementation
        logger.info(f"Using mock implementation for {tool_name}")
        
        # Simple mock implementations for different tools
        if tool_name == "dc_computer":
            action = tool_input.get("action", "unknown")
            if action == "screenshot":
                result = {"output": "Mock screenshot taken"}
            elif action == "move_mouse":
                coordinates = tool_input.get("coordinates", [0, 0])
                result = {"output": f"Mock mouse moved to {coordinates}"}
            elif action == "type_text":
                text = tool_input.get("text", "")
                result = {"output": f"Mock text typed: {text}"}
            else:
                result = {"output": f"Mock {action} executed"}
        elif tool_name == "dc_bash":
            command = tool_input.get("command", "")
            result = {"output": f"Mock command executed: {command}"}
        else:
            result = {"output": f"Mock execution of unknown tool: {tool_name}"}
        
        success = True
        
        # Record metrics
        if toggles.is_enabled("collect_metrics"):
            metrics.record_call(tool_name, tool_input, time.time() - start_time, success)
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        
        # Record metrics
        if toggles.is_enabled("collect_metrics"):
            metrics.record_call(tool_name, tool_input, duration, False)
            metrics.record_error(tool_name, tool_input, str(e))
        
        logger.error(f"Error in bridge execution: {str(e)}")
        return {"error": f"Error: {str(e)}"}

async def get_metrics() -> Dict[str, Any]:
    """Get the current metrics"""
    if toggles.is_enabled("collect_metrics"):
        return metrics.get_report()
    return {"error": "Metrics collection is disabled"}

async def set_feature_toggle(feature: str, enabled: bool) -> Dict[str, Any]:
    """Set a feature toggle"""
    try:
        toggles.set_feature(feature, enabled)
        return {
            "success": True,
            "message": f"Feature '{feature}' {'enabled' if enabled else 'disabled'}",
            "feature": feature,
            "enabled": enabled
        }
    except Exception as e:
        logger.error(f"Error setting feature toggle: {str(e)}")
        return {
            "success": False,
            "error": f"Error: {str(e)}",
            "feature": feature
        }

async def get_feature_toggles() -> Dict[str, bool]:
    """Get all feature toggles"""
    return toggles.toggles

async def clear_cache() -> Dict[str, Any]:
    """Clear the result cache"""
    try:
        cache.cache.clear()
        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }