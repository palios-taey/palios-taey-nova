import os
import math
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# Initialize Anthropic client (expects ANTHROPIC_API_KEY in environment)
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("Please set the ANTHROPIC_API_KEY environment variable.")
anthropic = Anthropic(api_key=api_key)

# Claude model to use (Claude 3 models support streaming, e.g., "claude-3-opus")
MODEL_NAME = "claude-3-opus"

# Token budget limits (Tier 2: ~5M input, 10M output per day).
# Adjust SESSION_HOURS if the application runs fewer hours to proportionally reduce the cap.
SESSION_HOURS = 24  # e.g., 24 for full-day, or 8 for work-day usage
DAILY_INPUT_LIMIT = 5_000_000   # Tier 2 daily input tokens
DAILY_OUTPUT_LIMIT = 10_000_000  # Tier 2 daily output tokens
MAX_INPUT_TOKENS_SESSION = int(DAILY_INPUT_LIMIT * (SESSION_HOURS / 24))
MAX_OUTPUT_TOKENS_SESSION = int(DAILY_OUTPUT_LIMIT * (SESSION_HOURS / 24))

# Max tokens per single Claude completion response (to avoid overly long outputs in one go)
MAX_TOKENS_TO_SAMPLE = 1000  # You can adjust this based on needed response length

# Initialize running token counters for the session
total_input_tokens = 0
total_output_tokens = 0

def estimate_token_count(text: str) -> int:
    """
    Roughly estimate the number of tokens in a given text.
    This uses a simple approximation: 1 token ≈ 4 characters or ≈1 word.
    For a more accurate count, integrate with a tokenization method or Anthropic's token count API.
    """
    # Using a simple word count as a proxy for token count
    # (Note: This is a coarse estimate; for exact counts, use Anthropic's counting API or a tokenizer)
    return max(1, math.ceil(len(text) / 4))

def truncate_prompt(prompt: str, max_tokens: int) -> str:
    """
    Truncate the prompt to ensure it does not exceed max_tokens (approximate).
    We’ll cut from the beginning if it's too long, keeping the end part (likely most relevant for user query).
    """
    # Approximate current token count
    tokens = estimate_token_count(prompt)
    if tokens <= max_tokens:
        return prompt  # no truncation needed
    # If too long, truncate from the front: remove excess tokens worth of characters
    # This is a simplistic approach; a smarter approach could remove oldest conversation history if multi-turn.
    excess = tokens - max_tokens
    # Estimate characters to remove (4 chars per token as approximation)
    chars_to_remove = excess * 4
    return prompt[chars_to_remove:]

if __name__ == "__main__":
    print("Starting Claude DC console. Type your prompt and press Enter. Type 'exit' or Ctrl+C to quit.")
    try:
        while True:
            user_input = input("\nUser: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                print("Exiting Claude DC console. Goodbye!")
                break

            # Estimate and manage token usage for the input
            user_tokens = estimate_token_count(user_input)
            if user_tokens + total_input_tokens > MAX_INPUT_TOKENS_SESSION:
                # If this input would exceed the session's input token cap, warn and possibly truncate or skip
                print("[Warning] Input prompt is too large or session input token limit reached. Truncating prompt...")
                # Truncate user_input to fit into remaining token budget
                remaining_tokens = max(0, MAX_INPUT_TOKENS_SESSION - total_input_tokens)
                user_input = truncate_prompt(user_input, remaining_tokens)
                user_tokens = estimate_token_count(user_input)
                if user_tokens == 0:
                    print("Unable to process input: token limit exceeded for this session.")
                    break  # break out if we cannot process any tokens

            # Update total input token count
            total_input_tokens += user_tokens

            # Formulate Claude prompt with Anthropic format
            prompt = f"{HUMAN_PROMPT} {user_input}{AI_PROMPT}"
            # (The HUMAN_PROMPT and AI_PROMPT include necessary tokens like "\n\nHuman:" and "\n\nAssistant:")

            # Initiate streaming completion from Claude
            try:
                response = anthropic.completions.create(
                    model=MODEL_NAME,
                    prompt=prompt,
                    max_tokens_to_sample=MAX_TOKENS_TO_SAMPLE,
                    stream=True,
                    stop_sequences=[HUMAN_PROMPT]  # stop when a new human prompt token would appear
                    # You can also adjust temperature or other params here if needed, e.g., temperature=1.0
                )
            except Exception as e:
                print(f"[Error] API call failed: {e}")
                break  # Break out on API errors (in a real scenario, implement retries or handle specific errors)

            # Stream and print Claude's response incrementally
            print("Claude:", end=" ", flush=True)  # prefix for Claude's response
            Claude_output_text = ""  # to accumulate Claude’s full response
            for chunk in response:
                # Each chunk is an object with the latest generated text (delta)
                chunk_text = getattr(chunk, "completion", chunk)  # handle if chunk is plain text vs object
                # Print the incremental text without newline (stay on same line)
                print(chunk_text, end="", flush=True)
                Claude_output_text += str(chunk_text)
            print()  # end the line after Claude's response is complete

            # Estimate tokens in Claude's output and update usage
            output_tokens = estimate_token_count(Claude_output_text)
            total_output_tokens += output_tokens

            # Enforce output token cap for session
            if total_output_tokens > MAX_OUTPUT_TOKENS_SESSION:
                print("[Warning] Reached the session output token limit. Further responses may be cut off or disabled.")
                # (In a real extension, you might stop the loop or reduce max_tokens_to_sample to avoid more usage)
    except KeyboardInterrupt:
        print("\nExiting Claude DC console. Goodbye!")

