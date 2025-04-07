import os
import uuid
import json
import subprocess
import time
import re
from pathlib import Path

# Directory setup
GROK_TRANSCRIPTS_DIR = Path("./transcripts/grok")
TEMP_DIR = Path("./transcripts/grok/temp_files")
INSIGHTS_DIR = Path("./transcripts/grok/combined_insights")
PROCESSED_DIR = Path("./transcripts/processed/grok")

# Ensure directories exist
for directory in [TEMP_DIR, INSIGHTS_DIR, PROCESSED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def get_speaker(header: str) -> str:
    """
    Determine the speaker from the header line using a flexible mapping.
    
    Args:
        header (str): The line or text that might indicate the speaker.
    
    Returns:
        str: "User", "Grok", or "Unknown".
    """
    speaker_map = {
        "User:": "User",
        "Human:": "User",
        "You:": "User",
        "Me:": "User",
        "Jesse:": "User",
        "Grok:": "Grok",
        "Assistant:": "Grok",
        "Bot:": "Grok",
    }
    header_lower = header.lower()
    for key, value in speaker_map.items():
        if key.lower() in header_lower:
            return value
    return "Unknown"

def extract_exchanges(content: str, file_path: Path) -> list[dict]:
    """
    Extract conversational exchanges from unstructured transcript content.
    
    Args:
        content (str): The raw text content of the transcript.
        file_path (Path): The path to the transcript file for logging.
    
    Returns:
        list[dict]: List of exchanges, each with "speaker" and "message".
    """
    # List of regex patterns to try, capturing speaker header and message
    patterns = [
        # Pattern 1: Common speaker markers (User:, Grok:, etc.)
        r'(?s)(User:|Human:|You:|Me:|Jesse:)(.*?)(?=User:|Human:|You:|Me:|Jesse:|Grok:|Assistant:|Bot:|$)',
        # Pattern 2: Grok-specific markers
        r'(?s)(Grok:|Assistant:|Bot:)(.*?)(?=User:|Human:|You:|Me:|Jesse:|Grok:|Assistant:|Bot:|$)',
        # Pattern 3: All-caps headers followed by colon (e.g., JESSE:)
        r'(?s)^([A-Z ]+:)(.*?)(?=\n[A-Z ]+:|$)',
        # Pattern 4: Timestamped lines (e.g., 14:30:00)
        r'(?s)^(\d{2}:\d{2}:\d{2})(.*?)(?=\n\d{2}:\d{2}:\d{2}|$)',
        # Pattern 5: Double newlines as separators
        r'(?s)(.+?)(?=\n\n|$)',
    ]
    
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, content))
        if len(matches) > 1:  # Require at least two exchanges for a pattern to be valid
            print(f"Using pattern {i+1} for {file_path.name}")
            exchanges = []
            for match in matches:
                if match.lastindex == 2:  # Two groups: header and message
                    header = match.group(1).strip()
                    message = match.group(2).strip()
                    speaker = get_speaker(header)
                elif match.lastindex == 1:  # One group: message only
                    message = match.group(1).strip()
                    speaker = "Unknown"
                else:
                    continue  # Skip if no groups
                exchanges.append({"speaker": speaker, "message": message})
            return exchanges
    
    # Fallback: Treat the entire content as a single exchange
    print(f"Using fallback for {file_path.name}")
    return [{"speaker": "Unknown", "message": content.strip()}]

def process_grok_file(file_path: Path) -> tuple[bool, str]:
    """
    Process a single Grok transcript file and generate insights.
    
    Args:
        file_path (Path): Path to the transcript file.
    
    Returns:
        tuple[bool, str]: (Success flag, Message).
    """
    try:
        # Read the file as plain text
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract exchanges
        exchanges = extract_exchanges(content, file_path)
        
        conversation_id = str(uuid.uuid4())
        exchange_insights = []
        
        # Process each exchange
        for idx, exchange in enumerate(exchanges):
            # Prepare temp input for edge_processor.py
            temp_input_file = TEMP_DIR / f"{conversation_id}_exchange_{idx}_temp.json"
            structured_data = {
                "data_id": f"{conversation_id}_exchange_{idx}",
                "content": [exchange["message"]],
                "source": "grok",
                "timestamp": time.time(),
                "data_type": "exchange",
                "metadata": {"speaker": exchange["speaker"], "exchange_index": idx}
            }
            with open(temp_input_file, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2)
            
            # Define expected output path from edge_processor.py
            insights_dir = PROCESSED_DIR / temp_input_file.stem
            insights_path = insights_dir / 'extracted_insights.json'
            
            # Run edge_processor.py
            result = subprocess.run(
                ['python3', 'edge_processor.py', str(temp_input_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Processing {file_path.name}, exchange {idx}: {result.stdout}")
            
            # Load insights
            if not insights_path.exists():
                return False, f"Insights not found at {insights_path}"
            with open(insights_path, 'r', encoding='utf-8') as f:
                insights = json.load(f)
            exchange_insights.append(insights)
        
        # Save combined insights
        combined_insights = {
            "conversation_id": conversation_id,
            "insights": exchange_insights,
            "timestamp": time.time()
        }
        output_file = INSIGHTS_DIR / f"{conversation_id}_combined_insights.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_insights, f, indent=2)
        
        return True, f"Processed {file_path.name} -> {output_file}"
    
    except Exception as e:
        return False, f"Error processing {file_path.name}: {str(e)}"

def main():
    """
    Main function to process all Grok transcripts.
    """
    processed = 0
    failed = 0
    
    print(f"Processing transcripts in {GROK_TRANSCRIPTS_DIR}")
    for file in sorted(GROK_TRANSCRIPTS_DIR.glob("*.txt")):
        print(f"\nWorking on: {file.name}")
        success, message = process_grok_file(file)
        print(message)
        if success:
            processed += 1
        else:
            failed += 1
    
    print(f"\nDone! Processed: {processed}, Failed: {failed}")

if __name__ == "__main__":
    main()
