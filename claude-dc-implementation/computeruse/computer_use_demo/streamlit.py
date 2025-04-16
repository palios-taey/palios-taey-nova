import os
import math
import streamlit as st
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# Page title and description
st.title("Claude DC – Streaming Chat Interface")
st.markdown("Enter a prompt for Claude and receive a streamed response. "
            "Token usage is tracked to avoid exceeding Tier 2 limits.")

# Initialize Anthropic client (API key from environment)
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    st.error("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    st.stop()
anthropic = Anthropic(api_key=api_key)
MODEL_NAME = "claude-3-7-sonnet-20250219"

# Token budget configuration (similar to loop.py)
SESSION_HOURS = 24  # adjust this if the app runs for less than a full day
DAILY_INPUT_LIMIT = 5_000_000
DAILY_OUTPUT_LIMIT = 10_000_000
MAX_INPUT_TOKENS_SESSION = int(DAILY_INPUT_LIMIT * (SESSION_HOURS / 24))
MAX_OUTPUT_TOKENS_SESSION = int(DAILY_OUTPUT_LIMIT * (SESSION_HOURS / 24))
MAX_TOKENS_TO_SAMPLE = 12000  # max tokens for Claude's reply in one go

# Initialize or retrieve session token counters
if "total_input_tokens" not in st.session_state:
    st.session_state["total_input_tokens"] = 0
if "total_output_tokens" not in st.session_state:
    st.session_state["total_output_tokens"] = 0

def estimate_token_count(text: str) -> int:
    """Approximate the token count of text (used for budgeting)."""
    return max(1, math.ceil(len(text) / 4))

def truncate_prompt(prompt: str, max_tokens: int) -> str:
    """Truncate prompt to not exceed max_tokens (approximate)."""
    tokens = estimate_token_count(prompt)
    if tokens <= max_tokens:
        return prompt
    # Remove excess tokens from the start of the prompt
    excess = tokens - max_tokens
    chars_to_remove = excess * 4
    return prompt[chars_to_remove:]

# User input area in the app
user_input = st.text_area("Your Prompt:", value="", placeholder="Type your question or request here...")

# Button to submit the prompt
if st.button("Submit"):
    if not user_input.strip():
        st.warning("Please enter a prompt before submitting.")
    else:
        # Token management for input prompt
        user_tokens = estimate_token_count(user_input)
        if user_tokens + st.session_state.total_input_tokens > MAX_INPUT_TOKENS_SESSION:
            st.warning("Input prompt is too long or session token budget nearly exceeded. The prompt will be truncated.")
            remaining_tokens = max(0, MAX_INPUT_TOKENS_SESSION - st.session_state.total_input_tokens)
            user_input = truncate_prompt(user_input, remaining_tokens)
            user_tokens = estimate_token_count(user_input)
            if user_tokens == 0:
                st.error("Cannot process prompt: session input token limit reached.")
                st.stop()
        # Update token count for input
        st.session_state.total_input_tokens += user_tokens

        # Prepare prompt for Claude with Anthropic formatting
        prompt = f"{HUMAN_PROMPT} {user_input}{AI_PROMPT}"

        # Display the prompt and a placeholder for the response
        st.write(f"**Prompt:** {user_input}")
        output_placeholder = st.empty()  # Placeholder for Claude's streaming output

        # Call Claude with streaming
        try:
            response = anthropic.completions.create(
                model=MODEL_NAME,
                prompt=prompt,
                max_tokens_to_sample=MAX_TOKENS_TO_SAMPLE,
                stream=True,
                stop_sequences=[HUMAN_PROMPT]
            )
        except Exception as e:
            st.error(f"Error during Claude API call: {e}")
            st.stop()

        # Stream the response in the placeholder
        full_response = ""
        for chunk in response:
            chunk_text = getattr(chunk, "completion", str(chunk))
            full_response += str(chunk_text)
            # Update the placeholder with the latest content (using Markdown for formatting)
            output_placeholder.markdown(f"**Claude:** {full_response}")
        # After streaming is done, we have the full response in full_response

        # Update output token count
        output_tokens = estimate_token_count(full_response)
        st.session_state.total_output_tokens += output_tokens

        # Check output token budget
        if st.session_state.total_output_tokens > MAX_OUTPUT_TOKENS_SESSION:
            st.warning("The session has reached the output token limit. Further queries might be limited.")

        # Optionally, display token usage stats to the user
        st.info(f"**Session Token Usage:** Input ~{st.session_state.total_input_tokens} tokens, "
                f"Output ~{st.session_state.total_output_tokens} tokens.")

