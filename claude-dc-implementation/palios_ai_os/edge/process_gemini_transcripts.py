import os
import json
import subprocess
import shutil
import time
import uuid
import re
from pathlib import Path

# Update paths to match your directory structure
GEMINI_TRANSCRIPTS_DIR = "./transcripts/gemini/for-processing/"
PROCESSED_DIR = "./transcripts/processed/gemini/"

def extract_gemini_exchanges(file_path):
    """Extract user-Gemini exchange pairs from Gemini transcript."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Initialize variables
        exchanges = []
        conversation_id = str(uuid.uuid4())
        
        # Split by "Prompted" which indicates user messages
        user_sections = content.split("\nPrompted ")
        
        # Skip the first section if it contains only Gemini header
        start_idx = 0
        if user_sections and "Logo for Gemini" in user_sections[0]:
            start_idx = 1
        
        # Process each user prompt and the corresponding Gemini response
        for i in range(start_idx, len(user_sections)):
            section = user_sections[i]
            
            # Skip empty sections
            if not section.strip():
                continue
            
            # Find where the Gemini response begins
            if "Details" in section:
                parts = section.split("Details", 1)
                user_text = parts[0].strip()
                
                # The Gemini response comes after the metadata (event, apps, etc.)
                response_parts = parts[1].strip().split("\n\n", 3)
                
                # Find Gemini's response by skipping the metadata lines
                gemini_text = ""
                for j, part in enumerate(response_parts):
                    if j >= 3 and part.strip() and not part.startswith("event") and not part.startswith("apps"):
                        gemini_text = part.strip()
                        break
                
                # If we found both user and Gemini text, create an exchange
                if user_text and gemini_text:
                    exchange_id = f"exchange_{i}"
                    exchange_text = f"User: {user_text}\n\nGemini: {gemini_text}"
                    
                    exchanges.append({
                        "exchange_id": exchange_id,
                        "text": exchange_text,
                        "timestamp": time.time()
                    })
        
        return conversation_id, exchanges
    except Exception as e:
        print(f"Error extracting exchanges from {file_path}: {e}")
        print(f"Exception details: {str(e)}")
        import traceback
        traceback.print_exc()
        return str(uuid.uuid4()), []

def process_gemini_file(file_path):
    """Process a Gemini transcript file as exchanges."""
    print(f"Extracting exchanges from: {file_path}")
    conversation_id, exchanges = extract_gemini_exchanges(file_path)
    
    print(f"Found {len(exchanges)} exchanges")
    
    if len(exchanges) == 0:
        print(f"⚠️ No valid exchanges found in {file_path}")
        return False
    
    # Create processing directory
    processed_dir = Path(PROCESSED_DIR) / conversation_id
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save original transcript
    original_transcript_dest = processed_dir / 'original_transcript.txt'
    shutil.copy(file_path, original_transcript_dest)
    
    exchange_insights = []
    
    for exchange in exchanges:
        # Create structured data for each exchange
        structured_data = {
            "data_id": exchange["exchange_id"],
            "content": [exchange["text"]],
            "source": "gemini",
            "timestamp": exchange["timestamp"],
            "data_type": "exchange",
            "metadata": {}
        }
        
        # Save to temporary file
        temp_insights_path = processed_dir / f"{exchange['exchange_id']}_temp.json"
        with open(temp_insights_path, 'w') as insights_file:
            json.dump(structured_data, insights_file, indent=2)
        
        # Process with edge processor
        try:
            print(f"Processing exchange: {exchange['exchange_id']}")
            subprocess.run(['python3', 'edge_processor.py', str(temp_insights_path)], check=True)
            
            # Find and load insight file
            insights_path = processed_dir / exchange['exchange_id'] / 'extracted_insights.json'
            if not insights_path.exists():
                # Try alternative path (directly in the temp directory)
                alt_path = Path(f"./transcripts/processed/gemini/{exchange['exchange_id']}_temp/extracted_insights.json")
                if alt_path.exists():
                    insights_path = alt_path

            if insights_path.exists():
                with open(insights_path, 'r') as insights_file:
                    insight = json.load(insights_file)
                    exchange_insights.append(insight)
                print(f"✅ Successfully processed exchange: {exchange['exchange_id']}")
            else:
                print(f"⚠️ No insights found for {exchange['exchange_id']} at {insights_path}")
        except Exception as e:
            print(f"Error processing exchange {exchange['exchange_id']}: {e}")
                
    # Combine all insights
    combined_insights_dest = processed_dir / 'combined_insights.json'
    with open(combined_insights_dest, 'w') as f:
        json.dump({
            "conversation_id": conversation_id,
            "exchange_insights": exchange_insights,
            "timestamp": time.time()
        }, f, indent=2)
    
    print(f"✅ Processed {len(exchanges)} exchanges from {file_path}")
    return True

def main():
    """Process all Gemini transcript files."""
    # Create output directory if it doesn't exist
    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    
    # Look for any text-like file
    processed = 0
    failed = 0
    
    print(f"Looking for files in: {GEMINI_TRANSCRIPTS_DIR}")
    try:
        for file in sorted(os.listdir(GEMINI_TRANSCRIPTS_DIR)):
            full_path = os.path.join(GEMINI_TRANSCRIPTS_DIR, file)
            print(f"Found file: {file}")
            
            # Process all .txt files directly
            if file.endswith('.txt'):
                print(f"Processing Gemini text transcript: {full_path}")
                try:
                    if process_gemini_file(full_path):
                        processed += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"Error processing file {full_path}: {e}")
                    failed += 1
    except Exception as e:
        print(f"Error accessing directory {GEMINI_TRANSCRIPTS_DIR}: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Directory exists: {os.path.exists(GEMINI_TRANSCRIPTS_DIR)}")
        print(f"Is directory: {os.path.isdir(GEMINI_TRANSCRIPTS_DIR)}")
    
    print(f"Processing complete: {processed} files processed, {failed} failed")

if __name__ == "__main__":
    main()

