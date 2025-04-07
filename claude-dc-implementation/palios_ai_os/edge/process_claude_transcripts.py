import os
import json
import subprocess
import shutil
import time
import uuid
from pathlib import Path

CLAUDE_TRANSCRIPTS_DIR = "./transcripts/claude/"

def extract_claude_content(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    all_conversations = []

    for convo in data:
        conversation_id = convo.get('uuid', str(uuid.uuid4()))
        messages = []

        for msg in convo.get('chat_messages', []):
            msg_content = msg.get('content', [])
            text = " ".join([content.get('text', '') for content in msg_content if content.get('type') == 'text'])

            messages.append({
                "message_id": msg.get('uuid', str(uuid.uuid4())),
                "text": text,
                "author": msg.get('sender', 'unknown'),
                "timestamp": msg.get('created_at', 'NA')
            })

        all_conversations.append((conversation_id, messages))

    return all_conversations

def process_claude_file(file_path):
    conversations = extract_claude_content(file_path)

    for conversation_id, messages in conversations:
        if messages:
            message_insights = []
            processed_dir = Path("./transcripts/processed/claude") / conversation_id
            processed_dir.mkdir(parents=True, exist_ok=True)

            # Preserve original file
            original_transcript_dest = processed_dir / 'original_transcript.json'
            shutil.move(file_path, original_transcript_dest)

            # Explicitly process each message separately
            for msg in messages:
                structured_data = {
                    "data_id": msg["message_id"],
                    "content": [msg["text"]],
                    "source": "claude",
                    "timestamp": msg["timestamp"],
                    "data_type": "message",
                    "metadata": {"author": msg["author"]}
                }

                temp_insights_path = processed_dir / f"{msg['message_id']}_temp.json"
                with open(temp_insights_path, 'w') as insights_file:
                    json.dump(structured_data, insights_file, indent=2)

                subprocess.run(['python3', 'edge_processor.py', str(temp_insights_path)], check=True)

                # Explicitly locate message insights
                insights_path = processed_dir / msg['message_id'] / 'extracted_insights.json'
                if insights_path.exists():
                    with open(insights_path, 'r') as insights_file:
                        insight = json.load(insights_file)
                        message_insights.append(insight)

            # Combine all message insights explicitly into a single conversation-level file
            combined_insights_dest = processed_dir / 'combined_insights.json'
            with open(combined_insights_dest, 'w') as f:
                json.dump({
                    "conversation_id": conversation_id,
                    "message_insights": message_insights,
                    "timestamp": time.time()
                }, f, indent=2)

            print(f"✅ Explicitly processed and combined insights at: {processed_dir}")

def main():
    for file in sorted(os.listdir(CLAUDE_TRANSCRIPTS_DIR)):
        full_path = os.path.join(CLAUDE_TRANSCRIPTS_DIR, file)

        if file.endswith('.json'):
            try:
                print(f"Processing Claude file: {full_path}")
                process_claude_file(full_path)
            except Exception as e:
                print(f"Error processing {full_path}: {e}")

if __name__ == "__main__":
    main()

