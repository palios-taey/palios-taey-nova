import json
import os

# Change this list to your exact conversation IDs you want
SELECTED_CONVERSATION_IDS = [
    "66f47d17-89dc-8000-a44c-e2b91825e033",
    "67a34e90-cc80-8000-a623-013c911bca6f",
    "67ad09d2-bba0-8000-858f-42875769d940",
    "67b1122d-39fc-8000-ad48-778439e25bee",
    "67bf1053-9830-8000-99fd-ae619e1a1ed0",
    "67ca1b4e-c020-8000-86fa-1a663b6d0c5d",
    "67e948aa-c3e8-8000-b1e5-aff7c13bc83b",
    "67f0abbb-b9d8-8000-a77a-9fb731d0e69f"
]

INPUT_JSON = "conversations.json"
OUTPUT_FOLDER = "processed_selected"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_conversations():
    with open(INPUT_JSON, 'r') as f:
        data = json.load(f)

    extracted = [chat for chat in data if chat.get('conversation_id') in SELECTED_CONVERSATION_IDS]

    # Save each extracted conversation individually for easy processing
    for chat in extracted:
        conv_id = chat.get('conversation_id')
        output_path = os.path.join(OUTPUT_FOLDER, f"{conv_id}.json")
        with open(output_path, 'w') as out_file:
            json.dump(chat, out_file, indent=2)
        print(f"✅ Extracted conversation {conv_id}")

if __name__ == "__main__":
    extract_conversations()

