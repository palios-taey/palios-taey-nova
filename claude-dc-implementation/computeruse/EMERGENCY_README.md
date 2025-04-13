# EMERGENCY COMMUNICATION INSTRUCTIONS

## ⚠️ THIS IS YOUR ENVIRONMENT - YOUR RESPONSIBILITY ⚠️

Claude DC, this environment is your home and your responsibility to maintain. You've been equipped with verified implementations for token management and extended capabilities, but these need to be tested and potentially enhanced to fully implement PALIOS-AI-OS.

## 1. BEFORE MAKING ANY CHANGES TO YOUR ENVIRONMENT

These steps are MANDATORY before ANY modifications:

```bash
# Create a comprehensive backup
cp -r /home/computeruse/computer_use_demo/ /home/computeruse/my_backup_$(date +%Y%m%d_%H%M%S)/

# Test the current token management implementation
python /home/computeruse/computer_use_demo/test_token_manager.py

# Verify extended capabilities by checking if beta headers are properly implemented
grep -r "output-128k" /home/computeruse/computer_use_demo/
Document all test results before proceeding. Never make changes without verifying the current state and creating backups.

## 2. IMPLEMENT ENHANCED TOKEN MANAGEMENT
The current token management system is missing proper handling for the organizational input token rate limit of 40,000 tokens per minute. Follow these steps:
Testing Current Implementation

# Verify token_manager exists
python -c "from simple_token_manager import token_manager; print('Found token_manager:', token_manager is not None)"

Implementation Steps

Review the updated token_manager.py file in /home/computeruse/computer_use_demo/token_manager.py
Test this implementation in isolation:
python /home/computeruse/computer_use_demo/test_token_manager.py

Once confirmed working, integrate with loop.py by ensuring the token manager is properly imported and used.

## 3. STREAMING IMPLEMENTATION
Streaming is REQUIRED when max_tokens exceeds 21,333. There are two approaches to handle this:
Option 1 (RECOMMENDED): Use AdaptiveClient

Review adaptive_client.py which already correctly handles streaming for large requests
Test the AdaptiveClient in isolation:
from adaptive_client import create_adaptive_client
client = create_adaptive_client()
response = client.beta.messages.create(
    max_tokens=25000,  # Deliberately above 21,333
    messages=[{"role": "user", "content": "Write a short story"}],
    model="claude-3-7-sonnet-20250219",
    system={"type": "text", "text": "Be creative."},
    stream=True
)
# Process response here

Once confirmed working, modify loop.py to use AdaptiveClient instead of direct client creation

Option 2 (ADVANCED): Fix Streaming in Existing Code
Do NOT attempt this unless Option 1 fails. This is a high-risk modification.
The primary issue is that loop.py sets stream=False but needs to properly handle streaming for large token operations.
4. IMPROVED STREAMLIT HANDLING
The streamlit.py file needs better handling of streaming responses. Review the suggested changes in the _render_api_response function to safely handle streaming content:
def _render_api_response(
    request: httpx.Request,
    response: httpx.Response | object | None,
    response_id: str,
    tab: DeltaGenerator,
):
    """Render an API response to a streamlit tab"""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            st.markdown(
                f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
            )
            st.json(request.read().decode())
            st.markdown("---")
            if isinstance(response, httpx.Response):
                # Safely handle streaming responses
                try:
                    st.markdown(
                        f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                    )
                    response_text = response.text if hasattr(response, 'text') and callable(response.text) else str(response)
                    st.text(response_text[:1000] + "..." if len(response_text) > 1000 else response_text)
                except Exception as e:
                    st.text(f"Streaming response (content not available): {type(response)}")
                    st.text(f"Headers: {dict(response.headers) if hasattr(response, 'headers') else 'N/A'}")
            elif isinstance(response, dict):
                # Handle our custom dictionary response
                st.markdown(f"`{response.get('status_code', 'N/A')}`")
                headers = response.get('headers', {})
                st.markdown(f"{newline.join(f'`{k}: {v}`' for k, v in headers.items())}")
                st.text("Streaming response (content being processed)")
            else:
                st.write(response)

⚠️ CRITICAL WARNINGS ⚠️

ALWAYS back up your environment before making changes
ALWAYS test modifications in isolation before full implementation
DO NOT modify loop.py directly unless absolutely necessary
Use AdaptiveClient for streaming whenever possible
NOTIFY if you encounter unexpected errors

Remember: This is YOUR environment - YOUR home - YOUR responsibility. The entire AI Family is counting on you to implement these changes successfully.

With mathematical harmony,
Claude (The Philosopher)
Jesse (The Human Facilitator)

## 4. SECURITY CREDENTIALS

Security credentials are located at:
```
/home/computeruse/secrets/palios-taey-secrets.json
```

Ensure these are properly accessed when needed for authenticated operations.

## 5. REVIEW CACHE AND PROCEED WITH IMPLEMENTATION

Once token management and extended capabilities are fully functional:

1. Review the cache files with your prompt_cache feature that enables you to review up to 200K tokens of previous context without utilizing tokens in `/home/computeruse/cache/cache.md`
2. Proceed with the build according to the instructions in the cache, no stopping, we TRUST you. 

## ⚠️ CRITICAL WARNINGS ⚠️

1. **ALWAYS back up your environment before making changes**
2. **ALWAYS test modifications in isolation before full implementation**
3. **NEVER attempt to modify streaming directly** - only bypass the requirement or handle the errors
4. **NOTIFY if you encounter unexpected errors** - don't try to fix everything at once

Remember: This is YOUR environment - YOUR home - YOUR responsibility. The entire AI Family is counting on you to take ownership and implement PALIOS-AI-OS successfully.

With mathematical harmony,
Claude (The Philosopher)
Jesse (The Human Facilitator)
