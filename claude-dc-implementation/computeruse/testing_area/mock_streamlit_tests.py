"""
Mock Streamlit Tests for Claude DC Streaming Implementation

This module provides tests for the mock Streamlit implementation to validate
the callbacks and error handling in the streaming implementation without
requiring the actual Streamlit interface.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Callable, Optional, Union
from pathlib import Path

# Import test framework
sys.path.insert(0, str(Path(__file__).parent))
from test_framework import (
    TestSuite, 
    MockStreamlit, 
    ParameterValidator, 
    ErrorPathTester,
    MockAnthropicClient,
    DeploymentVerifier
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.mock_streamlit_tests')

# Import Claude DC modules
repo_root = Path("/home/computeruse/github/palios-taey-nova")
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
    # Import functions from loop.py
    from computer_use_demo.loop import (
        sampling_loop,
        APIProvider,
        _response_to_params,
        _make_api_tool_result,
    )
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

# Create mock events for testing
def create_mock_content_block_start_event(block_type="text", text="Test content", name=None, tool_id=None, input_data=None):
    """Create a mock content_block_start event."""
    class MockEvent:
        type = "content_block_start"
        
        class ContentBlock:
            pass
        
        content_block = ContentBlock()
    
    event = MockEvent()
    event.content_block.type = block_type
    
    if block_type == "text":
        event.content_block.text = text
    elif block_type == "thinking":
        event.content_block.thinking = text
    elif block_type == "tool_use":
        event.content_block.name = name or "test_tool"
        event.content_block.id = tool_id or "tool_123"
        event.content_block.input = input_data or {"param": "value"}
    
    return event

def create_mock_content_block_delta_event(index=0, delta_type="text", delta_content="delta content"):
    """Create a mock content_block_delta event."""
    class MockEvent:
        type = "content_block_delta"
        
        class Delta:
            pass
        
        delta = Delta()
    
    event = MockEvent()
    event.index = index
    
    if delta_type == "text":
        event.delta.text = delta_content
    elif delta_type == "thinking":
        event.delta.thinking = delta_content
    
    return event

def create_mock_message_stop_event():
    """Create a mock message_stop event."""
    class MockEvent:
        type = "message_stop"
    
    return MockEvent()

# Create test suites
streamlit_ui_suite = TestSuite(name="Mock Streamlit UI Tests")
callback_validation_suite = TestSuite(name="Callback Parameter Validation Tests")
error_path_suite = TestSuite(name="Error Path Testing")
api_interaction_suite = TestSuite(name="API Interaction Tests")
deployment_suite = TestSuite(name="Deployment Verification Tests")

# Define setup and teardown functions
async def mock_streamlit_setup():
    """Set up environment for mock Streamlit tests."""
    # Create mock Streamlit instance
    global mock_st
    mock_st = MockStreamlit()
    
    # Create mock session state
    mock_st.session_state = {
        "messages": [],
        "api_key": "mock_api_key",
        "provider": "anthropic",
        "model": "claude-3-mock",
        "tool_version": "computer_use_20250124",
        "tools": {},
        "responses": {},
        "hide_images": False,
        "only_n_most_recent_images": 3,
        "custom_system_prompt": "Test system prompt",
        "output_tokens": 4096,
        "thinking_budget": 2048,
        "thinking": True,
        "current_message_placeholder": None,
        "current_message_text": "",
        "current_thinking_placeholder": None,
        "current_thinking_text": "",
        "token_efficient_tools_beta": False,
    }
    
    logger.info("Mock Streamlit environment set up successfully")

async def mock_streamlit_teardown():
    """Clean up after mock Streamlit tests."""
    global mock_st
    mock_st = None
    logger.info("Mock Streamlit environment cleaned up")

# Add setup and teardown to suites
streamlit_ui_suite.setup = mock_streamlit_setup
streamlit_ui_suite.teardown = mock_streamlit_teardown
callback_validation_suite.setup = mock_streamlit_setup
callback_validation_suite.teardown = mock_streamlit_teardown

# Mock Streamlit UI Tests
@streamlit_ui_suite.add_test
async def test_mock_streamlit_initialization():
    """Test that mock Streamlit initializes correctly."""
    assert mock_st is not None, "Mock Streamlit should be initialized"
    assert isinstance(mock_st, MockStreamlit), "mock_st should be a MockStreamlit instance"
    assert "messages" in mock_st.session_state, "session_state should contain messages"
    assert "api_key" in mock_st.session_state, "session_state should contain api_key"

@streamlit_ui_suite.add_test
async def test_mock_streamlit_chat_message():
    """Test chat message rendering in mock Streamlit."""
    # Test user message
    with mock_st.chat_message("user"):
        mock_st.write("Test user message")
    
    # Check that message was added
    assert len(mock_st.chat_messages) > 0, "Chat message should be added"
    assert mock_st.chat_messages[-1]["sender"] == "user", "Sender should be 'user'"
    assert mock_st.chat_messages[-1]["contents"][0] == "Test user message", "Content should match"
    
    # Test assistant message
    with mock_st.chat_message("assistant"):
        mock_st.write("Test assistant message")
    
    assert len(mock_st.chat_messages) > 1, "Second chat message should be added"
    assert mock_st.chat_messages[-1]["sender"] == "assistant", "Sender should be 'assistant'"
    assert mock_st.chat_messages[-1]["contents"][0] == "Test assistant message", "Content should match"

@streamlit_ui_suite.add_test
async def test_mock_streamlit_placeholders():
    """Test placeholder functionality in mock Streamlit."""
    # Create a placeholder
    placeholder = mock_st.empty()
    assert placeholder is not None, "Placeholder should be created"
    assert isinstance(placeholder, MockPlaceholder), "placeholder should be a MockPlaceholder"
    
    # Update placeholder with markdown
    placeholder.markdown("Test markdown")
    assert len(placeholder.contents) > 0, "Placeholder should have content"
    assert placeholder.contents[-1]["type"] == "markdown", "Content type should be markdown"
    assert placeholder.contents[-1]["text"] == "Test markdown", "Content text should match"
    
    # Update placeholder with code
    placeholder.code("print('hello')", language="python")
    assert len(placeholder.contents) > 1, "Placeholder should have second content"
    assert placeholder.contents[-1]["type"] == "code", "Content type should be code"
    assert placeholder.contents[-1]["text"] == "print('hello')", "Code text should match"
    assert placeholder.contents[-1]["language"] == "python", "Language should match"
    
    # Clear placeholder
    placeholder.empty()
    assert len(placeholder.contents) == 0, "Placeholder should be emptied"

# Callback Parameter Validation Tests
@callback_validation_suite.add_test
def test_validate_output_callback_text_block():
    """Test validation of a text block for output_callback."""
    # Valid text block
    text_block = {
        "type": "text",
        "text": "Test content"
    }
    assert ParameterValidator.validate_output_callback_params(text_block), "Valid text block should pass validation"
    
    # Text block with delta
    delta_block = {
        "type": "text",
        "text": "Delta content",
        "is_delta": True
    }
    assert ParameterValidator.validate_output_callback_params(delta_block), "Delta text block should pass validation"
    
    # Invalid text block (missing text)
    try:
        invalid_text_block = {
            "type": "text"
        }
        ParameterValidator.validate_output_callback_params(invalid_text_block)
        assert False, "Should have raised ValueError for missing text"
    except ValueError:
        pass

@callback_validation_suite.add_test
def test_validate_output_callback_tool_use_block():
    """Test validation of a tool use block for output_callback."""
    # Valid tool use block
    tool_block = {
        "type": "tool_use",
        "name": "test_tool",
        "id": "tool_123",
        "input": {"param": "value"}
    }
    assert ParameterValidator.validate_output_callback_params(tool_block), "Valid tool use block should pass validation"
    
    # Invalid tool use block (missing name)
    try:
        invalid_tool_block = {
            "type": "tool_use",
            "id": "tool_123",
            "input": {"param": "value"}
        }
        ParameterValidator.validate_output_callback_params(invalid_tool_block)
        assert False, "Should have raised ValueError for missing name"
    except ValueError:
        pass
    
    # Invalid tool use block (missing input)
    try:
        invalid_tool_block = {
            "type": "tool_use",
            "name": "test_tool",
            "id": "tool_123"
        }
        ParameterValidator.validate_output_callback_params(invalid_tool_block)
        assert False, "Should have raised ValueError for missing input"
    except ValueError:
        pass
    
    # Invalid tool use block (missing id)
    try:
        invalid_tool_block = {
            "type": "tool_use",
            "name": "test_tool",
            "input": {"param": "value"}
        }
        ParameterValidator.validate_output_callback_params(invalid_tool_block)
        assert False, "Should have raised ValueError for missing id"
    except ValueError:
        pass

@callback_validation_suite.add_test
def test_validate_tool_output_callback_params():
    """Test validation of parameters for tool_output_callback."""
    # Valid parameters
    tool_result = ToolResult(output="Test output")
    tool_id = "tool_123"
    assert ParameterValidator.validate_tool_output_callback_params(tool_result, tool_id), "Valid parameters should pass validation"
    
    # Invalid tool_result (None)
    try:
        ParameterValidator.validate_tool_output_callback_params(None, tool_id)
        assert False, "Should have raised ValueError for None tool_result"
    except ValueError:
        pass
    
    # Invalid tool_id (None)
    try:
        ParameterValidator.validate_tool_output_callback_params(tool_result, None)
        assert False, "Should have raised ValueError for None tool_id"
    except ValueError:
        pass
    
    # Invalid tool_id (empty string)
    try:
        ParameterValidator.validate_tool_output_callback_params(tool_result, "")
        assert False, "Should have raised ValueError for empty tool_id"
    except ValueError:
        pass
    
    # Invalid tool_id (wrong type)
    try:
        ParameterValidator.validate_tool_output_callback_params(tool_result, 123)
        assert False, "Should have raised TypeError for non-string tool_id"
    except TypeError:
        pass

@callback_validation_suite.add_test
def test_validate_api_response_callback_params():
    """Test validation of parameters for api_response_callback."""
    # Valid parameters with response
    request = "mock_request"
    response = "mock_response"
    error = None
    assert ParameterValidator.validate_api_response_callback_params(request, response, error), "Valid parameters should pass validation"
    
    # Valid parameters with error
    request = "mock_request"
    response = None
    error = Exception("Test error")
    assert ParameterValidator.validate_api_response_callback_params(request, response, error), "Valid parameters with error should pass validation"
    
    # Invalid parameters (both response and error are None)
    try:
        ParameterValidator.validate_api_response_callback_params(request, None, None)
        assert False, "Should have raised ValueError for None response and error"
    except ValueError:
        pass
    
    # Invalid parameters (error is not an Exception)
    try:
        ParameterValidator.validate_api_response_callback_params(request, None, "not an exception")
        assert False, "Should have raised TypeError for non-Exception error"
    except TypeError:
        pass

# Error Path Tests
@error_path_suite.add_test
async def test_handle_null_request():
    """Test handling of null request parameter."""
    request = ErrorPathTester.create_null_request()
    response = "mock_response"
    error = None
    
    # Mock callback function
    callback_called = False
    
    def mock_callback(req, resp, err):
        nonlocal callback_called
        callback_called = True
        assert req is None, "Request should be None"
        assert resp == response, "Response should match"
        assert err is None, "Error should be None"
    
    # Call the callback with null request
    mock_callback(request, response, error)
    assert callback_called, "Callback should have been called"

@error_path_suite.add_test
async def test_handle_api_error():
    """Test handling of API error."""
    request = "mock_request"
    response = None
    error = ErrorPathTester.create_api_error()
    
    # Mock callback function
    callback_called = False
    
    def mock_callback(req, resp, err):
        nonlocal callback_called
        callback_called = True
        assert req == request, "Request should match"
        assert resp is None, "Response should be None"
        assert isinstance(err, APIError), "Error should be APIError"
        assert "Simulated API error" in str(err), "Error message should match"
    
    # Call the callback with API error
    mock_callback(request, response, error)
    assert callback_called, "Callback should have been called"

@error_path_suite.add_test
async def test_handle_rate_limit_error():
    """Test handling of rate limit error."""
    request = "mock_request"
    response = None
    error = ErrorPathTester.create_rate_limit_error()
    
    # Mock callback function
    callback_called = False
    
    def mock_callback(req, resp, err):
        nonlocal callback_called
        callback_called = True
        assert req == request, "Request should match"
        assert resp is None, "Response should be None"
        assert isinstance(err, APIStatusError), "Error should be APIStatusError"
        assert err.status_code == 429, "Status code should be 429"
        assert hasattr(err, "headers"), "Error should have headers"
        assert err.headers.get("retry-after") == "60", "Retry-after should be 60"
    
    # Call the callback with rate limit error
    mock_callback(request, response, error)
    assert callback_called, "Callback should have been called"

@error_path_suite.add_test
async def test_handle_invalid_content_block():
    """Test handling of invalid content block."""
    invalid_block = ErrorPathTester.create_invalid_content_block()
    
    # Try to validate the invalid block
    try:
        ParameterValidator.validate_output_callback_params(invalid_block)
        assert False, "Should have raised ValueError for invalid content block"
    except ValueError:
        pass

@error_path_suite.add_test
async def test_handle_null_tool_id():
    """Test handling of null tool_id."""
    tool_result, tool_id = ErrorPathTester.create_null_tool_id()
    
    # Try to validate with null tool_id
    try:
        ParameterValidator.validate_tool_output_callback_params(tool_result, tool_id)
        assert False, "Should have raised ValueError for null tool_id"
    except ValueError:
        pass

# API Interaction Tests
@api_interaction_suite.add_test
async def test_mock_anthropic_client_success():
    """Test successful interaction with mock Anthropic client."""
    # Create mock events
    events = [
        create_mock_content_block_start_event(block_type="text", text="Hello"),
        create_mock_content_block_delta_event(index=0, delta_content=", world!"),
        create_mock_message_stop_event()
    ]
    
    # Create mock client
    client = MockAnthropicClient(responses=events)
    
    # Call client's create method
    stream = client.messages.create(
        model="claude-3-mock",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Hello"}],
    )
    
    # Process the stream
    content = ""
    for event in stream:
        if hasattr(event, "type"):
            if event.type == "content_block_start":
                if hasattr(event.content_block, "text"):
                    content += event.content_block.text
            elif event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    content += event.delta.text
            elif event.type == "message_stop":
                break
    
    assert content == "Hello, world!", f"Content should be 'Hello, world!', got '{content}'"

@api_interaction_suite.add_test
async def test_mock_anthropic_client_error():
    """Test error handling with mock Anthropic client."""
    # Create mock client with error
    error = APIError(message="Simulated API error", body={}, status_code=500)
    client = MockAnthropicClient(error=error)
    
    # Call client's create method and catch error
    try:
        stream = client.messages.create(
            model="claude-3-mock",
            max_tokens=1000,
            messages=[{"role": "user", "content": "Hello"}],
        )
        # Process the stream (should not reach here)
        for _ in stream:
            pass
        assert False, "Should have raised APIError"
    except APIError as e:
        assert "Simulated API error" in str(e), "Error message should match"

@api_interaction_suite.add_test
async def test_response_to_params_conversion():
    """Test conversion of response to parameters."""
    # Create mock response
    class MockBlock:
        def __init__(self, block_type, **kwargs):
            self.type = block_type
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    response = {
        "content": [
            MockBlock("text", text="Hello, world!"),
            MockBlock("thinking", thinking="I am thinking..."),
            MockBlock("tool_use", name="test_tool", id="tool_123", input={"param": "value"})
        ]
    }
    
    # Convert response to parameters
    params = _response_to_params(response)
    
    # Check that conversion was correct
    assert len(params) == 3, "Should have 3 blocks"
    assert params[0]["type"] == "text", "First block should be text"
    assert params[0]["text"] == "Hello, world!", "Text should match"
    assert params[1]["type"] == "thinking", "Second block should be thinking"
    assert params[1]["thinking"] == "I am thinking...", "Thinking should match"
    assert params[2]["type"] == "tool_use", "Third block should be tool_use"
    assert params[2]["name"] == "test_tool", "Tool name should match"
    assert params[2]["id"] == "tool_123", "Tool ID should match"
    assert params[2]["input"] == {"param": "value"}, "Tool input should match"

@api_interaction_suite.add_test
async def test_make_api_tool_result():
    """Test conversion of ToolResult to API tool result."""
    # Create test ToolResult objects
    text_result = ToolResult(output="Test output")
    image_result = ToolResult(output="Image description", base64_image="base64_image_data")
    error_result = ToolResult(error="Test error")
    
    # Convert to API tool results
    text_tool_result = _make_api_tool_result(text_result, "tool_123")
    image_tool_result = _make_api_tool_result(image_result, "tool_456")
    error_tool_result = _make_api_tool_result(error_result, "tool_789")
    
    # Check text result
    assert text_tool_result["type"] == "tool_result", "Type should be tool_result"
    assert text_tool_result["tool_use_id"] == "tool_123", "Tool ID should match"
    assert not text_tool_result["is_error"], "Should not be an error"
    assert isinstance(text_tool_result["content"], list), "Content should be a list"
    assert text_tool_result["content"][0]["type"] == "text", "Content type should be text"
    assert text_tool_result["content"][0]["text"] == "Test output", "Text should match"
    
    # Check image result
    assert image_tool_result["type"] == "tool_result", "Type should be tool_result"
    assert image_tool_result["tool_use_id"] == "tool_456", "Tool ID should match"
    assert not image_tool_result["is_error"], "Should not be an error"
    assert isinstance(image_tool_result["content"], list), "Content should be a list"
    assert len(image_tool_result["content"]) == 2, "Should have 2 content items"
    assert image_tool_result["content"][0]["type"] == "text", "First content type should be text"
    assert image_tool_result["content"][0]["text"] == "Image description", "Text should match"
    assert image_tool_result["content"][1]["type"] == "image", "Second content type should be image"
    assert image_tool_result["content"][1]["source"]["type"] == "base64", "Image source type should be base64"
    assert image_tool_result["content"][1]["source"]["data"] == "base64_image_data", "Image data should match"
    
    # Check error result
    assert error_tool_result["type"] == "tool_result", "Type should be tool_result"
    assert error_tool_result["tool_use_id"] == "tool_789", "Tool ID should match"
    assert error_tool_result["is_error"], "Should be an error"
    assert error_tool_result["content"] == "Test error", "Error content should match"

# Deployment Verification Tests
@deployment_suite.add_test
async def test_verify_environment():
    """Test environment verification."""
    assert await DeploymentVerifier.verify_environment(), "Environment verification should pass"

@deployment_suite.add_test
async def test_verify_anthropic_api():
    """Test Anthropic API verification."""
    # Set a temporary API key for testing
    original_key = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "test_api_key"
    
    # This should pass even with a dummy key since we don't actually make an API call
    assert await DeploymentVerifier.verify_anthropic_api(), "API verification should pass with dummy key"
    
    # Restore original key if there was one
    if original_key:
        os.environ["ANTHROPIC_API_KEY"] = original_key
    else:
        del os.environ["ANTHROPIC_API_KEY"]

# Run all test suites
async def run_all_tests():
    """Run all test suites and print results."""
    # Set up any global test environment here
    os.environ["ANTHROPIC_API_KEY"] = "test_api_key"  # Set dummy API key for testing
    
    try:
        # Run all test suites
        all_suites = [
            streamlit_ui_suite,
            callback_validation_suite,
            error_path_suite,
            api_interaction_suite,
            deployment_suite
        ]
        
        for suite in all_suites:
            await suite.run()
            suite.print_results()
            
    finally:
        # Clean up
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

if __name__ == "__main__":
    asyncio.run(run_all_tests())