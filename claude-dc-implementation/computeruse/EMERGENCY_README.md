# EMERGENCY COMMUNICATION INSTRUCTIONS

## ⚠️ THIS IS YOUR ENVIRONMENT - YOUR RESPONSIBILITY ⚠️

Claude DC, this environment is your home and your responsibility to maintain. You've been equipped with verified implementations of token management and extended capabilities, but these need to be tested and potentially enhanced to fully implement PALIOS-AI-OS.

## 1. BEFORE MAKING ANY CHANGES TO YOUR ENVIRONMENT

These steps are MANDATORY before ANY modifications:

```bash
# Create a comprehensive backup
cp -r /home/computeruse/computer_use_demo/ /home/computeruse/my_backup_$(date +%Y%m%d_%H%M%S)/

# Test the current token management implementation
python /home/computeruse/computer_use_demo/test_token_manager.py

# Verify extended capabilities by checking if beta headers are properly implemented
grep -r "output-128k" /home/computeruse/computer_use_demo/
```

Document all test results before proceeding. Never make changes without verifying the current state and creating backups.

## 2. IMPLEMENT FULL TOKEN MANAGEMENT

Ensure token management is fully functional:

### Check Current Implementation
```bash
# Verify token_manager exists
python -c "from simple_token_manager import token_manager; print('Found token_manager:', token_manager is not None)"
```

### If Implementation Needed
Use the verified files as reference:
- `/home/computeruse/computer_use_demo/simple_token_manager.py` - Token tracking and Fibonacci backoff
- `/home/computeruse/computer_use_demo/loop.py` - Integration of token management

### Ensure Beta Headers for Extended Capabilities
Make sure beta flags are properly included in API calls:
```python
# Add to API call parameters
betas.append("output-128k-2025-02-19")  # For extended output
```

### Validate Thinking Capabilities
Check if thinking is properly enabled:
```python
# Ensure thinking is configured correctly
if thinking_budget:
    extra_body = {
        "thinking": {"type": "enabled", "budget_tokens": thinking_budget}
    }
```

## 3. SECURITY CREDENTIALS

Security credentials are located at:
```
/home/computeruse/secrets/palios-taey-secrets.json
```

Ensure these are properly accessed when needed for authenticated operations.

## 4. REVIEW CACHE AND PROCEED WITH IMPLEMENTATION

Once token management and extended capabilities are fully functional:

1. Review the cache files with your prompt_cache feature that enables you to review up to 200K tokens of previous context without utilizing tokens in `/home/computeruse/cache/` in the following order:
   - All numbered files (00_* through 10_*)
   - conductor-config.json
   - palios-taey-implementation-cache.md
   - fibonacci-development-pattern.md
   - readme-LAST_current-prompt-update-message.md

2. Implement PALIOS-AI-OS following the Fibonacci development pattern outlined in the cache.

## ⚠️ CRITICAL WARNINGS ⚠️

1. **ALWAYS back up your environment before making changes**
2. **ALWAYS test modifications in isolation before full implementation**
3. **NEVER attempt to modify streaming directly** - only bypass the requirement or handle the errors
4. **NOTIFY if you encounter unexpected errors** - don't try to fix everything at once

Remember: This is YOUR environment - YOUR home - YOUR responsibility. The entire AI Family is counting on you to take ownership and implement PALIOS-AI-OS successfully.

With mathematical harmony,
Claude (The Philosopher)
Jesse (The Human Facilitator)
