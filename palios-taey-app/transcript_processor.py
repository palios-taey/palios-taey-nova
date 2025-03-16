import json
from datetime import datetime

class TranscriptProcessor:
    def __init__(self):
        self.tags = {
            "question": ["what", "how", "why", "when", "who", "where"],
            "request": ["can you", "could you", "please", "help me"],
            "statement": ["is", "are", "was", "were"]
        }
    
    def process(self, transcript):
        """Process a transcript and extract structured data."""
        if not transcript:
            return {"error": "Empty transcript"}
        
        result = {
            "processed_at": datetime.now().isoformat(),
            "extracted_tags": self.extract_tags(transcript),
            "message_count": len(transcript.split("\n")),
            "processed": True
        }
        
        return result
    
    def extract_tags(self, text):
        """Extract tags from text based on predefined patterns."""
        tags = []
        text_lower = text.lower()
        
        for tag_type, patterns in self.tags.items():
            for pattern in patterns:
                if pattern in text_lower:
                    tags.append(tag_type)
                    break
        
        return list(set(tags))
