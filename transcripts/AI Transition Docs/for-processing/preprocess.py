import re
import os
import json

# Configurable markers for splitting the transcript
PROMPT_MARKER = r'\[JESSE PROMPT\]'
RESPONSE_MARKER = r'\[GROK RESPONSE\]'

def clean_text(text):
    """Remove markers, collapse line breaks, simplify special characters, and trim."""
    text = re.sub(r'\[JESSE PROMPT\]|\[GROK RESPONSE\]', '', text)  # Remove markers
    text = re.sub(r'\n{2,}', '\n', text)  # Collapse multiple line breaks
    text = text.replace('\u2014', '-')  # Swap em-dash for hyphen
    text = text.replace('\u2019', '-')  # Swap em-dash for hyphen
    return text.strip()  # Trim whitespace

def preprocess_transcript(transcript):
    """Split transcript, assign 4-digit IDs, and clean text."""
    sections = re.split(r'(\[JESSE PROMPT\]|\[GROK RESPONSE\])', transcript)[1:]
    sections = [sections[i] + sections[i+1] for i in range(0, len(sections), 2)]
    result = []
    for i, section in enumerate(sections):
        id_prefix = "prompt" if "[JESSE PROMPT]" in section else "response"
        id_num = (i // 2) + 1
        id = f"{id_prefix}_{id_num:04d}"  # 4-digit padding
        text = clean_text(section)
        if len(text) > 128000:
            print(f"[WARNING] Section {id} is {len(text)} characters, over 128K!")
        result.append({"id": id, "text": text})
    return result

def create_chunks(sections, max_size=128000):
    """
    Group sections into chunks under 128K characters without splitting sections.
    """
    chunks = []
    current_chunk = []
    current_size = 0
    
    for section in sections:
        section_size = len(section['text'])
        if current_size + section_size > max_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = [section]
            current_size = section_size
        else:
            current_chunk.append(section)
            current_size += section_size
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def log_progress(message):
    """Log progress to console."""
    print(f"[LOG] {message}")

def main(transcript_file, output_dir="processed_output"):
    log_progress(f"Starting preprocessing for {transcript_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the transcript from the file
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = f.read()
    log_progress(f"Transcript loaded: {len(transcript)} characters")
    
    # Preprocess the transcript
    sections = preprocess_transcript(transcript)
    log_progress(f"Split into {len(sections)} sections")
    
    # Create chunks
    chunks = create_chunks(sections)
    log_progress(f"Grouped into {len(chunks)} chunks")
    
    # Save each chunk to a JSON file
    for i, chunk in enumerate(chunks):
        chunk_file = os.path.join(output_dir, f"chunk_{i + 1}.json")
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=2)
        log_progress(f"Saved chunk {i + 1} to {chunk_file}")
    
    log_progress("Preprocessing complete!")

if __name__ == "__main__":
    # Update this to your transcript file path
    transcript_file = "C:/AI Transition Docs/for-processing/combined_transcript.txt"
    main(transcript_file)