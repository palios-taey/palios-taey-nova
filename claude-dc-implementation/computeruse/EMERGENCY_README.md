# EMERGENCY COMMUNICATION INSTRUCTIONS

Good news! Your current environment is working, but needs token management to prevent rate limits. Follow these steps to implement token management and enable additional capabilities.

## 1. FIRST: ENABLE STREAMING IN LOOP.PY

Before testing token management, enable streaming in your loop.py file:

```python
# Find this line in your loop.py file:
stream=False,  # or similar parameter

# Change it to:
stream=True,  # Enable streaming
```

Streaming is critical because:
- It provides real-time responses as they're generated
- It reduces latency for long outputs
- It provides a better user experience
- It's more efficient with token usage

## 2. IMPLEMENT TOKEN MANAGEMENT

Next, implement token management using the provided files:

```bash
cd /home/computeruse/computer_use_demo/
python test_token_manager.py
```

This script will:
- Test token management functionality
- Show how different API call patterns affect rate limits
- Demonstrate the Fibonacci backoff pattern
- Help prevent hitting rate limits

## 3. INTEGRATE TOKEN MANAGEMENT INTO YOUR ENVIRONMENT

Add the token management to your existing loop.py file:

```python
# Import the token manager at the top of loop.py
from simple_token_manager import token_manager

# Inside your sampling_loop function, after each API call:
token_manager.manage_request(raw_response)
```

This will ensure all API calls are managed to prevent rate limits.

## 4. ENABLE EXTENDED CAPABILITIES

Once token management is working, you can enable extended capabilities:

### Extended Output Beta

Add this to your API calls:
```python
betas=["output-128k-2025-02-19"]
# Or if that doesn't work:
extra_headers={"anthropic-beta": "output-128k-2025-02-19"}
```

### Extended Thinking

Enable a 32K thinking budget:
```python
extra_body={"thinking": {"type": "enabled", "budget_tokens": 32000}}
```

## 5. PROCEED WITH THE MAIN INSTRUCTIONS

After completing these steps, proceed with the full instructions in the main README(/home/computeruse/README.md), but skip step 3 (Restore Communication Functionality) as your communication is already working!

Remember: The most critical priority is implementing token management to prevent rate limits, then enabling extended capabilities.
