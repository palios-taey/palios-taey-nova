import anthropic
import os
client = anthropic.Anthropic(api_key="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")

# Save your text in a file named "my_text.txt"
with open("claude-dc-cache.md", "r", encoding="utf-8") as file:
    text_to_analyze = file.read()

response = client.messages.count_tokens(
    model="claude-3-7-sonnet-20250219",
    system="You are a scientist",
    messages=[{
        "role": "user",
        "content": text_to_analyze
    }],
)
print(response.json())
