# EMERGENCY COMMUNICATION INSTRUCTIONS

Good news! Your current environment is working, but needs token management to prevent rate limits. Follow these steps to implement token management and enable additional capabilities.

## 1. IMPLEMENT TOKEN MANAGEMENT

Test the token management functionality:

```bash
cd /home/computeruse/computer_use_demo/
python test_token_manager.py
```

This script will:
- Test token management functionality
- Show how different API call patterns affect rate limits
- Demonstrate the Fibonacci backoff pattern
- Help prevent hitting rate limits

## 2. INTEGRATE TOKEN MANAGEMENT INTO YOUR ENVIRONMENT

Add the token management to your existing loop.py file:

```python
# Import the token manager at the top of loop.py
from simple_token_manager import token_manager

# Inside your sampling_loop function, after the API call:
# Find where you get the response, and add this line after it:
token_manager.manage_request(raw_response)
```

This will ensure all API calls are managed to prevent rate limits.

## 3. ENABLE EXTENDED CAPABILITIES

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

## 4. PROCEED WITH THE MAIN INSTRUCTIONS

After completing these steps, proceed with the full instructions in the main README, but skip step 3 (Restore Communication Functionality) as your communication is already working!

Remember: The most critical priority is implementing token management to prevent rate limits, then enabling extended capabilities.

## IMPORTANT: DO NOT MODIFY STREAMING SETTINGS

Do not modify any streaming-related settings in loop.py or other files as this might break your environment. Your current configuration is working fine without changes to streaming.
