# Phase 2 Implementation Plan

## Overview

This implementation plan follows DCCC's specified approach for safely adding Phase 2 enhancements to the Claude DC system. Following the "YOUR Environment = YOUR Home = YOUR Responsibility" framework, all changes will be thoroughly tested in isolation before being considered for production deployment.

## Environment Variables

```bash
# Feature flags
export ENABLE_STREAMING=false
export ENABLE_PROMPT_CACHE=false
export ENABLE_EXTENDED_OUTPUT=false

# Constants
export MAX_TOKENS=16384
export THINKING_BUDGET=12000

# Paths
export TEST_ENV=/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/testing_area
export PROD_ENV=/home/computeruse/computer_use_demo
```

## Implementation Sequence

### 1. Create Feature Flags (ENV vars)

- Implement environment variable checks in loop.py
- Add conditional code paths for each feature
- Create default fallbacks when features are disabled

```python
# Sample feature flag implementation
ENABLE_STREAMING = os.environ.get('ENABLE_STREAMING', '').lower() in ('true', 't', 'yes', 'y', '1')
ENABLE_PROMPT_CACHE = os.environ.get('ENABLE_PROMPT_CACHE', '').lower() in ('true', 't', 'yes', 'y', '1')
ENABLE_EXTENDED_OUTPUT = os.environ.get('ENABLE_EXTENDED_OUTPUT', '').lower() in ('true', 't', 'yes', 'y', '1')

# Constants with environment overrides
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '16384'))
THINKING_BUDGET = int(os.environ.get('THINKING_BUDGET', '12000'))
```

### 2. Implement Minimal MVP Per Feature

#### Streaming Implementation (MVP)
- Add `stream=True` parameter to API calls
- Implement basic event handling for content blocks
- Add minimal UI updates for streaming tokens

#### Prompt Cache Implementation (MVP)
- Add cache control to system message
- Implement cache breakpoints for recent messages
- Add the prompt-caching-2024-07-31 beta flag

#### Extended Output Implementation (MVP)
- Update max_tokens parameter handling
- Add validation for token limits
- Implement UI updates for longer responses

### 3. Add Error Handling + Fallbacks

#### API Error Handling
- Implement try/except blocks for all beta flags
- Add fallbacks for unsupported parameters
- Create graceful degradation when features fail

#### Tool Validation
- Add parameter validation for all tool calls
- Implement default parameters for missing values
- Add detailed logging for debugging

#### Context Preservation
- Implement state saving before restarts
- Add state restoration mechanism
- Create structured transition prompts

### 4. Deploy to TEST

```bash
# Deploy steps
cp ${TEST_ENV}/modified_loop.py ${TEST_ENV}/deployments/
cp ${TEST_ENV}/modified_streamlit.py ${TEST_ENV}/deployments/

# Test with feature flags
ENABLE_STREAMING=true python3 ${TEST_ENV}/deployments/test_harness.py
```

### 5. Validation: 25 Test Cases

Run the full test suite with all combinations of features:
```bash
# Run all tests
python3 ${TEST_ENV}/test_suite.py --verbose

# Run individual feature tests
python3 ${TEST_ENV}/stream/stream_test.py
python3 ${TEST_ENV}/stream/stream_tool_test.py
python3 ${TEST_ENV}/cache/cache_test.py
python3 ${TEST_ENV}/output/output_test.py
python3 ${TEST_ENV}/integration_test.py
```

### 6. Document Success Metrics

For each feature, document:
- Performance improvements
- Token usage statistics
- Error rates
- User experience improvements
- Compatibility with different prompts and tools

### 7. Final Steps Before Production

```bash
# Final sequence
git add modified_files
git commit -m "Phase 2 enhancements: streaming, prompt cache, extended output"
git push origin feature/phase2-enhancements

# After human review and approval
cp ${TEST_ENV}/validated_loop.py ${PROD_ENV}/loop.py
cp ${TEST_ENV}/validated_streamlit.py ${PROD_ENV}/streamlit.py
```

## Key Fixes Implementation

### Handle API Type Errors Gracefully

```python
try:
    # Try with all parameters
    stream = client.messages.create(**api_params)
except TypeError as e:
    # If beta parameter causes issues, remove it and retry
    if "got an unexpected keyword argument 'beta'" in str(e):
        logger.warning("Beta parameter not supported, removing it and retrying")
        api_params.pop('beta', None)
        stream = client.messages.create(**api_params)
    else:
        # Other TypeError, handle appropriately
        logger.error(f"TypeError in API call: {e}")
        # Use fallback mechanism
```

### Add Try/Except on Beta Flag Usage

```python
# Safely add beta flags
beta_flags = []
try:
    if ENABLE_PROMPT_CACHE:
        beta_flags.append("prompt-caching-2024-07-31")
    if ENABLE_TOOLS:
        beta_flags.append("computer-use-2025-01-24")
    
    if beta_flags:
        api_params["beta"] = beta_flags
except Exception as e:
    logger.warning(f"Failed to add beta flags: {e}")
    # Continue without beta flags
```

### Implement Delayed Tool Execution

```python
# Handle tool execution with appropriate delays
for block in content_blocks:
    if getattr(block, "type", "") == "tool_use":
        tool_name = getattr(block, "name", "")
        tool_id = getattr(block, "id", "")
        tool_input = getattr(block, "input", {})
        
        logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
        
        # Add delay to ensure UI is updated before tool execution
        await asyncio.sleep(0.5)
        
        # Run the tool with proper error handling
        try:
            result = await tool_collection.run(
                name=tool_name,
                tool_input=tool_input,
            )
            tool_output_callback(result, tool_id)
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            error_result = ToolResult(error=str(e))
            tool_output_callback(error_result, tool_id)
```

### Create Context Preservation Strategy

```python
def save_context(output_path):
    """Save the current conversation context."""
    try:
        # Extract key information
        context = {
            "messages": st.session_state.messages,
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "features_enabled": {
                    "streaming": ENABLE_STREAMING,
                    "prompt_cache": ENABLE_PROMPT_CACHE,
                    "extended_output": ENABLE_EXTENDED_OUTPUT
                }
            }
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(context, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error saving context: {e}")
        return False

def restore_context(input_path):
    """Restore conversation context."""
    try:
        with open(input_path, 'r') as f:
            context = json.load(f)
        
        # Restore messages
        st.session_state.messages = context["messages"]
        
        # Log metadata
        logger.info(f"Restored context from: {context['metadata']['saved_at']}")
        
        return True
    except Exception as e:
        logger.error(f"Error restoring context: {e}")
        return False
```

## Safety Constraints Implementation

### Never Directly Modify PROD

All changes will be made in the testing environment first:
```bash
# Safe modification approach
TEST_ENV=/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/testing_area
PROD_ENV=/home/computeruse/computer_use_demo

# 1. Copy production file to test env
cp ${PROD_ENV}/loop.py ${TEST_ENV}/loop.py.orig

# 2. Make modifications in test env
vi ${TEST_ENV}/loop.py.orig

# 3. Test modifications
python ${TEST_ENV}/test_script.py

# 4. Only after validation and human review, copy to prod
# cp ${TEST_ENV}/validated_loop.py ${PROD_ENV}/loop.py
```

### Feature Flag Testability

All features will be implemented behind feature flags:
```python
# In loop.py
def sampling_loop(...):
    # Feature flags
    use_streaming = os.environ.get('ENABLE_STREAMING', '').lower() in ('true', 't', 'yes', 'y', '1')
    use_prompt_cache = os.environ.get('ENABLE_PROMPT_CACHE', '').lower() in ('true', 't', 'yes', 'y', '1')
    use_extended_output = os.environ.get('ENABLE_EXTENDED_OUTPUT', '').lower() in ('true', 't', 'yes', 'y', '1')
    
    # Apply feature flags
    if use_streaming:
        # Streaming implementation
        api_params["stream"] = True
    
    if use_prompt_cache:
        # Prompt cache implementation
        try:
            beta_flags.append("prompt-caching-2024-07-31")
            system[0]["cache_control"] = {"type": "ephemeral"}
        except Exception as e:
            logger.warning(f"Failed to enable prompt caching: {e}")
    
    if use_extended_output:
        # Use extended token limit
        api_params["max_tokens"] = MAX_TOKENS
    else:
        # Use default token limit
        api_params["max_tokens"] = 4096
```

## Validation Process

### Run Test Suite with Verbose Flag

```bash
# Full test suite validation
python3 ${TEST_ENV}/test_suite.py --verbose --log-level=DEBUG

# Check coverage of all features
python3 ${TEST_ENV}/test_suite.py --feature=streaming
python3 ${TEST_ENV}/test_suite.py --feature=prompt_cache
python3 ${TEST_ENV}/test_suite.py --feature=extended_output
python3 ${TEST_ENV}/test_suite.py --feature=all
```

### Error Log Monitoring

```bash
# Check error logs
grep -i error ${TEST_ENV}/logs/*.log

# Check warning logs
grep -i warning ${TEST_ENV}/logs/*.log

# Check beta flag issues
grep -i "beta" ${TEST_ENV}/logs/*.log | grep -i "error\|warning\|fail"
```

### Token Usage Monitoring

```python
# Track token usage
class TokenUsageMonitor:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.requests = 0
    
    def record_usage(self, request, response):
        """Record token usage from API response."""
        if response and hasattr(response, "usage"):
            self.input_tokens += getattr(response.usage, "input_tokens", 0)
            self.output_tokens += getattr(response.usage, "output_tokens", 0)
            self.total_tokens = self.input_tokens + self.output_tokens
            self.requests += 1
            
            logger.info(f"Token usage - Input: {self.input_tokens}, Output: {self.output_tokens}, Total: {self.total_tokens}, Requests: {self.requests}")

# Usage
token_monitor = TokenUsageMonitor()
token_monitor.record_usage(request, response)
```

### Context Preservation Verification

```bash
# Test context preservation
python3 ${TEST_ENV}/test_context_preservation.py --save-context
# Restart Streamlit
python3 ${TEST_ENV}/test_context_preservation.py --restore-context

# Verify preservation
python3 ${TEST_ENV}/test_context_preservation.py --verify-context
```

## Implementation Timeline

1. Day 1: Set up testing environment and implement feature flags
2. Day 2: Implement and test streaming MVP
3. Day 3: Implement and test prompt caching MVP
4. Day 4: Implement and test extended output MVP
5. Day 5: Integrate features and run comprehensive tests
6. Day 6: Document results and prepare for review
7. Day 7: Address review feedback and prepare for production

## Success Criteria

The implementation will be considered successful when:
1. All tests pass with no errors
2. Performance metrics show improvements
3. User experience is enhanced by streaming responses
4. Token usage is optimized by prompt caching
5. Extended output enables more comprehensive responses
6. All safety constraints are verified
7. Context is preserved across restarts

## Conclusion

This implementation plan follows DCCC's specifications and focuses on safety, reliability, and thorough testing before any production deployment. By adhering to the "YOUR Environment = YOUR Home = YOUR Responsibility" framework, we ensure that Claude DC's core functionality is protected throughout the enhancement process.