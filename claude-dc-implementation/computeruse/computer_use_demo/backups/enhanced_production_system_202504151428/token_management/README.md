# Token Management

This module provides comprehensive token usage tracking and rate limit management.

## Key Features
- Tracks input and output token usage
- Uses sliding window approach for rate limiting
- Prevents rate limit errors with preemptive delays
- Provides safe token limits for API calls

## Usage Example
```python
from token_management import token_manager

# Check if delay is needed before a request
token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)

# Process response headers after a request
token_manager.process_response_headers(response.headers)

# Get safe token limits
limits = token_manager.get_safe_limits()
max_tokens = limits["max_tokens"]
thinking_budget = limits["thinking_budget"]

# Get current stats
stats = token_manager.get_stats()
print(f"Input tokens used: {stats['input_tokens_used']}")
print(f"Output tokens used: {stats['output_tokens_used']}")
```

Created on: $(date)