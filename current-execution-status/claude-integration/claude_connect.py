import os
import anthropic

# Set your API key as an environment variable before running
# export CLAUDE_API_KEY=your_key_here

# Get the API key from environment variable (safer approach)
api_key = os.environ.get("CLAUDE_API_KEY")

# Initialize the client
client = anthropic.Anthropic(api_key=api_key)

# Simple test message
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0,
    system="You are Claude, working from Jesse's System76 machine as 'The Conductor'.",
    messages=[
        {"role": "user", "content": "Hello Claude, are you connected to my System76 machine now?"}
    ]
)

# Print the response
print(message.content)
