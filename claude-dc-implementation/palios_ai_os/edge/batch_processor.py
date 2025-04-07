import os
import json
import subprocess
import uuid

TRANSCRIPTS_DIR = "./transcripts/"
TEMP_JSON_DIR = "./temp_json_chats/"

# Ensure temp directory exists
os.makedirs(TEMP_JSON_DIR, exist_ok=True)

def process_transcript(filepath):
    _, ext = os.path.splitext(filepath)

    if ext == '.json':
        with open(filepath, 'r') as file:
            data = json.load(file)

            # Check if data is a list (Claude JSON)
            if isinstance(data, list):
                for chat in data:
                    chat_id = chat.get('uuid') or chat.get('conversation_id') or chat.get('id') or str(uuid.uuid4())
                    temp_path = os.path.join(TEMP_JSON_DIR, f"{chat_id}.json")
                    with open(temp_path, 'w') as temp_file:
                        json.dump(chat, temp_file)
                    subprocess.run(['python3', 'edge_processor.py', temp_path], check=True)

            # Single JSON object (ChatGPT or other)
            elif isinstance(data, dict):
                chat_id = data.get('uuid') or data.get('conversation_id') or data.get('id') or str(uuid.uuid4())
                temp_path = os.path.join(TEMP_JSON_DIR, f"{chat_id}.json")
                with open(temp_path, 'w') as temp_file:
                    json.dump(data, temp_file)
                subprocess.run(['python3', 'edge_processor.py', temp_path], check=True)

            else:
                print(f"Unsupported JSON structure: {filepath}")

    elif ext == '.txt':
        subprocess.run(['python3', 'edge_processor.py', filepath], check=True)

    else:
        print(f"Skipping unsupported file: {filepath}")

def main():
    for root, _, files in os.walk(TRANSCRIPTS_DIR):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                print(f"Processing: {filepath}")
                process_transcript(filepath)
            except subprocess.CalledProcessError as e:
                print(f"Error processing {filepath}: {e}")
            except json.JSONDecodeError:
                print(f"JSON decoding failed for file: {filepath}")
            except Exception as e:
                print(f"Unexpected error processing {filepath}: {e}")

if __name__ == "__main__":
    main()
