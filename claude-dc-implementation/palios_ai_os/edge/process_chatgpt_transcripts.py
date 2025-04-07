import os
import json
import subprocess
import uuid
import shutil
import time
from pathlib import Path 

CHATGPT_TRANSCRIPTS_DIR = "./transcripts/chatgpt/"

def extract_chatgpt_content(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    conversation_id = data.get('conversation_id', str(uuid.uuid4()))
    conversations = []

    if 'mapping' in data and isinstance(data['mapping'], dict):
        for msg_id, msg_content in data['mapping'].items():
            message = msg_content.get('message')
            if message:
                text = message.get('content', {}).get('parts', [])
                if text:
                    conversations.append({
                        "message_id": msg_id,
                        "text": text,
                        "author": message.get('author', {}).get('role', 'unknown'),
                        "timestamp": message.get('create_time', 'NA')
                    })

    return conversation_id, conversations

def process_file(file_path):
    conversation_id, conversations = extract_chatgpt_content(file_path)

    if conversations:
        message_insights = []
        processed_dir = Path("./transcripts/processed/chatgpt") / conversation_id
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Move original transcript for historical integrity
        original_transcript_dest = processed_dir / 'original_transcript.json'
        shutil.move(file_path, original_transcript_dest)

        for convo in conversations:
            # Prepare structured data per message
            structured_data = {
                "data_id": convo["message_id"],
                "content": convo["text"],
                "source": "chatgpt",
                "timestamp": convo["timestamp"],
                "data_type": "message",
                "metadata": {"author": convo["author"]}
            }

            temp_insights_path = processed_dir / f"{convo['message_id']}_temp.json"
            with open(temp_insights_path, 'w') as insights_file:
                json.dump(structured_data, insights_file, indent=2)

            # Run edge_processor for each individual message
            subprocess.run(['python3', 'edge_processor.py', str(temp_insights_path)], check=True)

            # Load insights and delete temporary file afterward
            insights_path = processed_dir / convo['message_id'] / 'extracted_insights.json'
            if insights_path.exists():
                with open(insights_path, 'r') as insights_file:
                    insight = json.load(insights_file)
                    message_insights.append(insight)

                # Remove temp JSON
                temp_insights_path.unlink()

        # Combine all individual insights explicitly into a single file
        combined_insights_dest = processed_dir / 'combined_insights.json'
        with open(combined_insights_dest, 'w') as f:
            json.dump({
                "conversation_id": conversation_id,
                "message_insights": message_insights,
                "timestamp": time.time()
            }, f, indent=2)

        print(f"✅ Completed structured processing explicitly at: {processed_dir}")

    else:
        print(f"No valid conversations found in {file_path}")

def main():
    for file in sorted(os.listdir(CHATGPT_TRANSCRIPTS_DIR)):
        full_path = os.path.join(CHATGPT_TRANSCRIPTS_DIR, file)

        if file.endswith('.json'):
            try:
                print(f"Processing ChatGPT file: {full_path}")
                process_file(full_path)
            except Exception as e:
                print(f"Error processing {full_path}: {e}")

if __name__ == "__main__":
    main()

