import os
import sys
import json
import anthropic
from datetime import datetime

# Option 1: Set the API key in your code (not recommended for production)
client = anthropic.Anthropic(api_key="your-api-key")

# Option 2: Set the API key as an environment variable (better security)
# os.environ["ANTHROPIC_API_KEY"] = "your_api_key_here"
# client = anthropic.Anthropic()

# Continue with your token counting code...
with open("my_text.txt", "r", encoding="utf-8") as file:
    text_to_analyze = file.read()

response = client.messages.count_tokens(
    model="claude-3-7-sonnet-20250219",
    system="You are a scientist",
    messages=[{
        "role": "user",
        "content": text_to_analyze
    }],
)
print(response.token_count)  # Using token_count directly instead of response.json()
