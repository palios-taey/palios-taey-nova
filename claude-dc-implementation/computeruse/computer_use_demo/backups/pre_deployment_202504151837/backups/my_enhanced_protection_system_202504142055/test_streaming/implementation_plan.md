# Streaming Support Enhancement Implementation Plan

## Current Status Assessment

The current `streaming_client.py` implementation already includes:
- Basic integration with token management
- Support for streaming API calls
- Handling of the beta extended output flag
- Support for thinking budget

However, several critical aspects need enhancement to ensure stable operation during long-running tasks:

## Enhancement Goals

1. **Mandatory Streaming for Large Operations**
   - Current implementation includes a threshold check but needs stronger enforcement
   - Need to ALWAYS use streaming for operations exceeding 4096 tokens
   - Prevent any possibility of non-streaming large token operations

2. **Robust Error Handling and Recovery**
   - Implement exponential backoff retry mechanism for streaming errors
   - Handle network interruptions during long-running streaming operations
   - Recover gracefully from transient errors without losing context

3. **Tighter Integration with Other Protection Components**
   - Ensure consistent token tracking across all modules
   - Implement checks with token manager before initiating streaming operations
   - Integrate with safe file operations for handling large file content in API calls

4. **Enhanced Streaming Performance for Long-Running Tasks**
   - Optimize for operations lasting >10 minutes
   - Implement heartbeat mechanism to keep connections alive
   - Add progress tracking and reporting for long operations

5. **Comprehensive Error Event Handling**
   - Detect and handle various streaming error types
   - Maintain partial results when stream is interrupted
   - Implement resumable operations where possible

## Implementation Details

### 1. Mandatory Streaming Enforcement

```python
def calculate_streaming_requirement(self, max_tokens: int, thinking_budget: Optional[int] = None) -> bool:
    """Force streaming for all operations exceeding threshold"""
    # ALWAYS use streaming for operations exceeding 4096 tokens
    # Lower threshold from current implementation to ensure streaming for medium-large operations
    return max_tokens > 4096 or (thinking_budget is not None and thinking_budget > 4096)
```

Add enforcement in the `create_message` method:
```python
# Enforce streaming for large operations regardless of user preference
if max_tokens > 4096 or (thinking_budget is not None and thinking_budget > 4096):
    use_streaming = True
    logger.info("Enforcing streaming for large token operation")
```

### 2. Exponential Backoff Retry Mechanism

```python
def retry_with_exponential_backoff(self, operation_func, max_retries=3, base_delay=1.0):
    """Execute an operation with exponential backoff retries"""
    retries = 0
    while True:
        try:
            return operation_func()
        except Exception as e:
            retries += 1
            if retries > max_retries:
                raise
            delay = base_delay * (2 ** (retries - 1)) * (0.5 + random.random())
            logger.warning(f"Retry {retries}/{max_retries} after error: {e}. Waiting {delay:.2f}s")
            time.sleep(delay)
```

### 3. Integration with Token Manager and Safe Operations

Enhance the existing token manager integration with more detailed checks:

```python
def check_token_limits(self, estimated_input_tokens, estimated_output_tokens):
    """Check token limits and ensure we have capacity for operation"""
    if not has_token_manager:
        return True
        
    # Get current token usage
    input_tokens_per_minute = token_manager.input_tokens_per_minute
    input_limit = token_manager.org_input_limit
    
    # Calculate available capacity
    available_capacity = input_limit - input_tokens_per_minute
    
    # If estimated tokens would exceed capacity, we need to delay
    if estimated_input_tokens > available_capacity * 0.9:  # 90% of available capacity
        logger.warning(f"Operation requires {estimated_input_tokens} tokens but only {available_capacity} available")
        token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
        return self.check_token_limits(estimated_input_tokens, estimated_output_tokens)
    
    return True
```

### 4. Heartbeat Mechanism for Long-Running Operations

```python
def maintain_stream_connection(self, stream_object, heartbeat_interval=60):
    """Maintain stream connection during long-running operations"""
    last_activity = time.time()
    
    def heartbeat_thread():
        nonlocal last_activity
        while not getattr(stream_object, '_closed', True):
            time_since_activity = time.time() - last_activity
            if time_since_activity > heartbeat_interval:
                # Send heartbeat ping or no-op to keep connection alive
                try:
                    # Implementation depends on specific stream type
                    logger.debug(f"Sending heartbeat after {time_since_activity:.2f}s inactivity")
                    last_activity = time.time()
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
            time.sleep(heartbeat_interval / 2)
    
    thread = threading.Thread(target=heartbeat_thread, daemon=True)
    thread.start()
    return thread
```

### 5. Enhanced Progress Tracking

```python
class StreamProgressTracker:
    """Track progress of streaming operations"""
    
    def __init__(self, estimated_total_tokens=None):
        self.start_time = time.time()
        self.tokens_received = 0
        self.estimated_total = estimated_total_tokens
        self.last_update_time = self.start_time
        self.update_interval = 5  # seconds
        
    def update(self, new_tokens):
        """Update progress with newly received tokens"""
        self.tokens_received += new_tokens
        current_time = time.time()
        
        # Only log updates at certain intervals to avoid spam
        if current_time - self.last_update_time >= self.update_interval:
            elapsed = current_time - self.start_time
            tokens_per_second = self.tokens_received / elapsed if elapsed > 0 else 0
            
            if self.estimated_total:
                percent_complete = (self.tokens_received / self.estimated_total) * 100
                logger.info(f"Stream progress: {self.tokens_received}/{self.estimated_total} tokens "
                           f"({percent_complete:.1f}%) at {tokens_per_second:.1f} tokens/sec")
            else:
                logger.info(f"Stream progress: {self.tokens_received} tokens received "
                           f"at {tokens_per_second:.1f} tokens/sec")
            
            self.last_update_time = current_time
```

## Testing Strategy

1. **Long-Running Operations Test**
   - Create test cases that simulate operations running >10 minutes
   - Test with varied token sizes and operation types
   - Measure stability and token usage throughout operation

2. **Error Recovery Test**
   - Simulate connection errors during streaming operations
   - Verify retry mechanism works correctly
   - Ensure partial results are preserved

3. **Integration Test**
   - Verify interaction with token manager during long operations
   - Test integration with safe file operations for large files
   - Ensure consistent token tracking across modules

4. **Performance Monitoring**
   - Track token usage over time during streaming operations
   - Monitor memory usage for long-running streams
   - Measure recovery time after interruptions

## Expected Benefits

1. **Enhanced Stability**
   - Reliable operation for tasks running >10 minutes
   - Graceful recovery from transient errors
   - Prevention of timeout errors

2. **Better Resource Management**
   - Improved token usage tracking during streaming operations
   - Prevention of rate limit errors during long-running tasks
   - Efficient handling of large token operations

3. **Improved User Experience**
   - Progress updates during long operations
   - Minimal interruptions in service
   - Preservation of context and data during errors

This enhancement will ensure my environment's continued stable operation, especially during demanding, long-running tasks that previously might have timed out or encountered rate limit errors.