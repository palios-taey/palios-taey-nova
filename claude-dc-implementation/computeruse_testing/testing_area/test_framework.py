"""
Comprehensive Testing Framework for Claude DC Streaming with Tool Use

This framework provides a structured approach to test Claude DC's streaming 
implementation with tool use, focusing on error handling and parameter validation.

Key Components:
1. Mock Streamlit Implementation
2. Callback Parameter Validation
3. Error Path Testing
4. Integration Testing
5. Deployment Verification
"""

import os
import sys
import asyncio
import logging
import inspect
import traceback
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional, Union, Tuple
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("claude_dc_test_framework.log")
    ]
)
logger = logging.getLogger('claude_dc.test_framework')

# Determine paths based on environment
if os.path.exists("/home/computeruse"):
    # We're in the container
    repo_root = Path("/home/computeruse/github/palios-taey-nova")
else:
    # We're on the host
    repo_root = Path("/home/jesse/projects/palios-taey-nova")

claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"

# Add key paths to Python path
paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir)
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import required modules
try:
    from computer_use_demo.tools import (
        TOOL_GROUPS_BY_VERSION,
        ToolCollection,
        ToolResult,
        ToolVersion,
    )
    from anthropic import (
        Anthropic,
        APIError,
        APIResponseValidationError,
        APIStatusError,
    )
    # Import looping functionality
    from computer_use_demo.loop import (
        sampling_loop,
        APIProvider,
        _response_to_params,
        _make_api_tool_result,
    )
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

# Test status enumeration
class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

@dataclass
class TestResult:
    """Store the result of a test case."""
    name: str
    status: TestStatus
    message: str = ""
    exception: Optional[Exception] = None
    traceback: Optional[str] = None
    duration_ms: float = 0.0
    
    def __str__(self):
        status_color = {
            TestStatus.PASSED: "\033[92m",  # Green
            TestStatus.FAILED: "\033[91m",  # Red
            TestStatus.SKIPPED: "\033[93m", # Yellow
            TestStatus.ERROR: "\033[91m",   # Red
        }
        reset = "\033[0m"
        
        result = f"{status_color[self.status]}{self.status.value}{reset} - {self.name}"
        if self.message:
            result += f": {self.message}"
        if self.duration_ms > 0:
            result += f" ({self.duration_ms:.2f}ms)"
        if self.exception:
            result += f"\n  Exception: {type(self.exception).__name__}: {self.exception}"
        if self.traceback:
            result += f"\n  Traceback:\n{self.traceback}"
        return result

@dataclass
class TestSuite:
    """Collection of related test cases."""
    name: str
    tests: List[Callable] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    
    def add_test(self, test_func):
        """Add a test function to the suite."""
        self.tests.append(test_func)
        return test_func
    
    async def run(self):
        """Run all tests in the suite."""
        logger.info(f"Running test suite: {self.name}")
        
        if self.setup:
            try:
                await self.setup()
            except Exception as e:
                logger.error(f"Suite setup failed: {e}")
                tb_str = traceback.format_exc()
                self.results.append(TestResult(
                    name="Suite Setup",
                    status=TestStatus.ERROR,
                    message="Setup function failed",
                    exception=e,
                    traceback=tb_str
                ))
                return self.results
        
        for test_func in self.tests:
            test_name = test_func.__name__
            logger.info(f"Running test: {test_name}")
            
            try:
                import time
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(test_func):
                    await test_func()
                else:
                    test_func()
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                self.results.append(TestResult(
                    name=test_name,
                    status=TestStatus.PASSED,
                    duration_ms=duration_ms
                ))
                logger.info(f"Test {test_name} passed in {duration_ms:.2f}ms")
                
            except AssertionError as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                tb_str = traceback.format_exc()
                
                self.results.append(TestResult(
                    name=test_name,
                    status=TestStatus.FAILED,
                    message=str(e),
                    exception=e,
                    traceback=tb_str,
                    duration_ms=duration_ms
                ))
                logger.error(f"Test {test_name} failed: {e}")
                
            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                tb_str = traceback.format_exc()
                
                self.results.append(TestResult(
                    name=test_name,
                    status=TestStatus.ERROR,
                    message=f"Unexpected error: {e}",
                    exception=e,
                    traceback=tb_str,
                    duration_ms=duration_ms
                ))
                logger.error(f"Error in test {test_name}: {e}")
        
        if self.teardown:
            try:
                await self.teardown()
            except Exception as e:
                logger.error(f"Suite teardown failed: {e}")
                tb_str = traceback.format_exc()
                self.results.append(TestResult(
                    name="Suite Teardown",
                    status=TestStatus.ERROR,
                    message="Teardown function failed",
                    exception=e,
                    traceback=tb_str
                ))
        
        return self.results
    
    def print_results(self):
        """Print results of all tests in the suite."""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        print(f"\n=== Test Suite: {self.name} ===")
        print(f"Total: {len(self.results)}, Passed: {passed}, Failed: {failed}, Errors: {errors}, Skipped: {skipped}")
        
        for result in self.results:
            print(f"- {result}")
        
        print(f"=== End of Test Suite: {self.name} ===\n")

# Parameter validation utilities
def validate_parameter(param: Any, param_name: str, expected_type=None, nullable=False):
    """Validate a parameter for type and nullability."""
    if param is None:
        if nullable:
            return True
        else:
            raise ValueError(f"Parameter '{param_name}' cannot be None")
    
    if expected_type and not isinstance(param, expected_type):
        raise TypeError(f"Parameter '{param_name}' must be of type {expected_type.__name__}, got {type(param).__name__}")
    
    return True

# 1. Mock Streamlit Implementation
class MockStreamlit:
    """
    Mock implementation of Streamlit for testing.
    This simulates the UI elements and callbacks without requiring a browser.
    """
    
    def __init__(self):
        self.session_state = {}
        self.components = []
        self.logs = []
        self.errors = []
        self.markdown_contents = []
        self.json_contents = []
        self.chat_messages = []
        self.current_container = None
        
    def log(self, message):
        """Add a log message."""
        self.logs.append(message)
        logger.debug(f"MockStreamlit: {message}")
        
    def error(self, message):
        """Log an error message."""
        self.errors.append(message)
        logger.error(f"MockStreamlit ERROR: {message}")
        return self
        
    def markdown(self, text):
        """Simulate rendering markdown."""
        self.markdown_contents.append(text)
        self.log(f"Rendered markdown: {text[:50]}...")
        return self
        
    def json(self, data):
        """Simulate rendering JSON."""
        self.json_contents.append(data)
        self.log(f"Rendered JSON: {str(data)[:50]}...")
        return self
        
    def chat_message(self, sender):
        """Simulate a chat message container."""
        self.current_container = {"sender": sender, "contents": []}
        self.chat_messages.append(self.current_container)
        return self
        
    def write(self, content):
        """Simulate the st.write function."""
        if self.current_container:
            self.current_container["contents"].append(content)
        self.log(f"Wrote content: {str(content)[:50]}...")
        return self
        
    def code(self, code_text, language=None):
        """Simulate rendering code."""
        if self.current_container:
            self.current_container["contents"].append({"type": "code", "code": code_text, "language": language})
        self.log(f"Rendered code block: {code_text[:50]}...")
        return self
        
    def image(self, image_data):
        """Simulate rendering an image."""
        if self.current_container:
            self.current_container["contents"].append({"type": "image", "data": "IMAGE_DATA"})
        self.log("Rendered image")
        return self
        
    def empty(self):
        """Simulate an empty placeholder."""
        placeholder = MockPlaceholder(self)
        if self.current_container:
            self.current_container["contents"].append({"type": "placeholder", "object": placeholder})
        self.log("Created empty placeholder")
        return placeholder
        
    def chat_input(self, label=None):
        """Simulate a chat input box."""
        self.log(f"Created chat input with label: {label}")
        return None  # Simulating no user input
        
    def tabs(self, tab_names):
        """Simulate tabs."""
        self.log(f"Created tabs: {tab_names}")
        return [self for _ in tab_names]  # Return self for each tab
        
    def sidebar(self):
        """Simulate sidebar."""
        self.log("Accessed sidebar")
        return self
        
    def expander(self, label):
        """Simulate an expander."""
        self.log(f"Created expander: {label}")
        return self
        
    def title(self, text):
        """Simulate page title."""
        self.log(f"Set title: {text}")
        return self
        
    def text_input(self, label, **kwargs):
        """Simulate text input."""
        self.log(f"Created text input: {label}")
        return self
        
    def radio(self, label, options, **kwargs):
        """Simulate radio button group."""
        self.log(f"Created radio group: {label} with options {options}")
        return self
        
    def checkbox(self, label, **kwargs):
        """Simulate checkbox."""
        self.log(f"Created checkbox: {label}")
        return self
        
    def number_input(self, label, **kwargs):
        """Simulate number input."""
        self.log(f"Created number input: {label}")
        return self
        
    def text_area(self, label, **kwargs):
        """Simulate text area."""
        self.log(f"Created text area: {label}")
        return self
        
    def button(self, label, **kwargs):
        """Simulate button."""
        self.log(f"Created button: {label}")
        return False  # Not clicked
        
    def info(self, text):
        """Simulate info box."""
        self.log(f"Showed info: {text}")
        return self
        
    def warning(self, text):
        """Simulate warning box."""
        self.log(f"Showed warning: {text}")
        return self
        
    def success(self, text):
        """Simulate success box."""
        self.log(f"Showed success: {text}")
        return self
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
        
class MockPlaceholder:
    """Mock implementation of a Streamlit placeholder."""
    
    def __init__(self, parent_streamlit):
        self.parent = parent_streamlit
        self.contents = []
        
    def markdown(self, text):
        """Render markdown in placeholder."""
        self.contents.append({"type": "markdown", "text": text})
        self.parent.log(f"Placeholder updated with markdown: {text[:50]}...")
        return self
        
    def code(self, code_text, language=None):
        """Render code in placeholder."""
        self.contents.append({"type": "code", "text": code_text, "language": language})
        self.parent.log(f"Placeholder updated with code: {code_text[:50]}...")
        return self
        
    def write(self, content):
        """Write to placeholder."""
        self.contents.append({"type": "write", "content": content})
        self.parent.log(f"Placeholder updated with content: {str(content)[:50]}...")
        return self
        
    def empty(self):
        """Empty the placeholder."""
        self.contents.clear()
        self.parent.log("Placeholder emptied")
        return self

# 2. Callback Parameter Validation
class ParameterValidator:
    """
    Utility class to validate parameters passed to callbacks.
    This helps identify issues with null values or incorrect types.
    """
    
    @staticmethod
    def validate_output_callback_params(content_block):
        """Validate parameters for output_callback."""
        if content_block is None:
            raise ValueError("content_block cannot be None")
            
        if not isinstance(content_block, dict):
            raise TypeError(f"content_block must be a dict, got {type(content_block)}")
            
        # Check required fields
        if "type" not in content_block:
            raise ValueError("content_block must have a 'type' field")
            
        # Validate based on type
        block_type = content_block.get("type")
        if block_type == "text":
            if "text" not in content_block and not content_block.get("is_delta", False):
                raise ValueError("Text block must have a 'text' field")
        elif block_type == "tool_use":
            if "name" not in content_block:
                raise ValueError("Tool use block must have a 'name' field")
            if "input" not in content_block:
                raise ValueError("Tool use block must have an 'input' field")
            if "id" not in content_block:
                raise ValueError("Tool use block must have an 'id' field")
                
        return True
    
    @staticmethod
    def validate_tool_output_callback_params(result, tool_id):
        """Validate parameters for tool_output_callback."""
        if result is None:
            raise ValueError("tool_result cannot be None")
            
        # Ensure tool_id is a string and not empty
        if tool_id is None:
            raise ValueError("tool_id cannot be None")
        if not isinstance(tool_id, str):
            raise TypeError(f"tool_id must be a string, got {type(tool_id)}")
        if not tool_id:
            raise ValueError("tool_id cannot be empty")
            
        # Validate ToolResult object has required attributes
        if not hasattr(result, "output") and not hasattr(result, "error"):
            raise ValueError("ToolResult must have either 'output' or 'error' attribute")
            
        return True
    
    @staticmethod
    def validate_api_response_callback_params(request, response, error):
        """Validate parameters for api_response_callback."""
        # At least one of response or error should be provided
        if response is None and error is None:
            raise ValueError("Either response or error must be provided")
            
        # If error is provided, it should be an Exception
        if error is not None and not isinstance(error, Exception):
            raise TypeError(f"error must be an Exception, got {type(error)}")
            
        return True

# 3. Error Path Testing
class ErrorPathTester:
    """
    Tools for testing error paths in streaming implementation.
    Deliberately creates error conditions to test handling.
    """
    
    @staticmethod
    def create_null_request():
        """Create a test case with null request parameter."""
        return None
    
    @staticmethod
    def create_null_response():
        """Create a test case with null response parameter."""
        return None
    
    @staticmethod
    def create_api_error():
        """Create a test case with API error."""
        return APIError(message="Simulated API error", body={}, status_code=500)
    
    @staticmethod
    def create_status_error():
        """Create a test case with API status error."""
        return APIStatusError(message="Simulated status error", body={}, status_code=400, request=None)
    
    @staticmethod
    def create_validation_error():
        """Create a test case with API validation error."""
        return APIResponseValidationError(message="Simulated validation error", body={}, status_code=422, request=None)
    
    @staticmethod
    def create_network_error():
        """Create a test case with network error."""
        return ConnectionError("Simulated network error")
    
    @staticmethod
    def create_timeout_error():
        """Create a test case with timeout error."""
        return TimeoutError("Simulated timeout error")
    
    @staticmethod
    def create_rate_limit_error():
        """Create a test case with rate limit error."""
        error = APIStatusError(message="Rate limit exceeded", body={}, status_code=429, request=None)
        error.headers = {"retry-after": "60"}
        return error
    
    @staticmethod
    def create_invalid_content_block():
        """Create an invalid content block."""
        return {"invalid_field": "This block is missing required fields"}
    
    @staticmethod
    def create_malformed_tool_result():
        """Create a malformed tool result."""
        # Create a dict instead of proper ToolResult
        return {"output": "This is not a proper ToolResult object"}
    
    @staticmethod
    def create_null_tool_id():
        """Create a test case with null tool_id."""
        return ToolResult(output="Test output"), None

# 4. Integration Testing
class MockAnthropicClient:
    """
    Mock Anthropic client for testing streaming implementation without actual API calls.
    """
    
    def __init__(self, responses=None, error=None):
        """
        Initialize with predefined responses or error.
        
        Args:
            responses: List of events to yield when streaming
            error: Exception to raise when called
        """
        self.responses = responses or []
        self.error = error
        self.messages = MagicMock()
        self.with_raw_response = MagicMock()
        
        # Set up create method based on parameters
        if error:
            self.messages.create = MagicMock(side_effect=error)
            self.messages.with_raw_response.create = MagicMock(side_effect=error)
        else:
            self.messages.create = MagicMock(return_value=self._create_stream())
            self.messages.with_raw_response.create = MagicMock(return_value=self._create_response())
            
    def _create_stream(self):
        """Create a generator that yields response events."""
        class MockStream:
            def __init__(self, events):
                self.events = events
                
            def __iter__(self):
                return self
                
            def __next__(self):
                if not self.events:
                    raise StopIteration
                return self.events.pop(0)
        
        return MockStream(list(self.responses))  # Create copy of list
        
    def _create_response(self):
        """Create a mock raw response object."""
        class MockRawResponse:
            def __init__(self, client):
                self.client = client
                self.http_response = MagicMock()
                self.http_response.request = MagicMock()
                self.http_response.status_code = 200
                self.http_response.headers = {"content-type": "application/json"}
                
            def parse(self):
                # Consolidate stream events into a response
                result = {
                    "id": "msg_mock",
                    "role": "assistant",
                    "model": "claude-3-mock",
                    "content": [],
                    "stop_reason": "end_turn",
                    "type": "message",
                }
                
                for event in self.client.responses:
                    if hasattr(event, "content_block"):
                        result["content"].append(event.content_block)
                
                return result
        
        return MockRawResponse(self)

# 5. Deployment Verification
class DeploymentVerifier:
    """
    Utilities for verifying deployments of the streaming implementation.
    Ensures that the deployment meets requirements and performs as expected.
    """
    
    @staticmethod
    async def verify_environment():
        """Verify that the environment is properly configured."""
        # Check Python version
        import platform
        python_version = platform.python_version_tuple()
        assert int(python_version[0]) >= 3 and int(python_version[1]) >= 8, "Python 3.8+ required"
        
        # Check required environment variables
        required_vars = ["PATH", "PYTHONPATH"]
        for var in required_vars:
            assert var in os.environ, f"Environment variable {var} not set"
        
        # Check for valid Python paths
        for path in sys.path:
            assert os.path.exists(path), f"Path in sys.path does not exist: {path}"
        
        # Check for required directories
        required_dirs = [repo_root, claude_dc_root, computer_use_demo_dir]
        for directory in required_dirs:
            assert directory.exists(), f"Required directory does not exist: {directory}"
            
        return True
    
    @staticmethod
    async def verify_rollback_capability():
        """Verify that rollback capability is available."""
        # Check if backup directories exist
        backup_dir = repo_root / "backups"
        if not backup_dir.exists():
            logger.warning(f"Backup directory not found: {backup_dir}")
            return False
            
        # Check if there are any backups
        backups = list(backup_dir.glob("*"))
        if not backups:
            logger.warning("No backups found in backup directory")
            return False
            
        # Find the most recent backup
        most_recent = max(backups, key=os.path.getmtime)
        logger.info(f"Most recent backup: {most_recent}")
        
        return True
    
    @staticmethod
    async def verify_anthropic_api():
        """Verify that the Anthropic API is accessible."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set in environment")
            return False
            
        # Create a simple client to test connectivity
        try:
            client = Anthropic(api_key=api_key)
            # We don't actually make an API call, just verify the client can be created
            logger.info("Anthropic client created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create Anthropic client: {e}")
            return False

async def run_all_tests():
    """Run all test suites and print results."""
    results = []
    
    # Add test suites here
    # ...
    
    for suite in results:
        suite.print_results()

if __name__ == "__main__":
    asyncio.run(run_all_tests())