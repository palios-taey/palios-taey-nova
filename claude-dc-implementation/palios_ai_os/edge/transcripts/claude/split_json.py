import json
import os

def split_json(input_file, output_dir, chunk_size):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the large JSON file
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Determine the total number of items and split into chunks
    total_items = len(data)
    for i in range(0, total_items, chunk_size):
        chunk = data[i:i + chunk_size]
        output_file = os.path.join(output_dir, f'chunk_{i // chunk_size + 1}.json')
        with open(output_file, 'w', encoding='utf-8') as chunk_file:
            json.dump(chunk, chunk_file, indent=4)

        print(f"Created {output_file}")


# Usage example
input_file = 'transcripts/claude/conversations.json'  # <- Correct relative path
output_dir = 'transcripts/claude/claude_conversations_chunks'
chunk_size = 1  # Adjust the chunk size as needed

split_json(input_file, output_dir, chunk_size)
