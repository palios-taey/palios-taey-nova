#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Transcript Processor for the Conductor Framework
--------------------------------------------------------
This module provides a robust solution for processing AI transcripts from various
sources (Claude, ChatGPT, Grok, Gemini) and in different formats.

Features:
- Format-specific parsers for each AI system
- Chunking for large documents to avoid memory issues
- Improved JSON parsing with fallback strategies
- Detailed logging for debugging

Authors: Claude & Jesse
"""

import os
import json
import re
import logging
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Union
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_transcript_processor")

class EnhancedTranscriptProcessor:
    """Processor for AI transcripts from various sources and formats."""
    
    def __init__(self, spacy_model=None):
        """
        Initialize the processor.
        
        Args:
            spacy_model: Optional pre-loaded spaCy model
        """
        self.spacy_model = spacy_model
        
        # Load spaCy if needed and not provided
        if not self.spacy_model:
            try:
                import spacy
                self.spacy_model = spacy.load("en_core_web_md")
                logger.info("Loaded spaCy model: en_core_web_md")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {str(e)}")
                self.spacy_model = None
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 900000) -> List[str]:
        """
        Split text into manageable chunks for processing.
        
        Args:
            text: The text to split
            max_chunk_size: Maximum size of each chunk (characters)
            
        Returns:
            List of text chunks
        """
        # Check if splitting is needed
        if len(text) <= max_chunk_size:
            return [text]
            
        # Try to split on paragraph boundaries
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit, start a new chunk
            if len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # If any chunk is still too large, split it by character
        result = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                # Split by characters
                for i in range(0, len(chunk), max_chunk_size):
                    result.append(chunk[i:i+max_chunk_size])
            else:
                result.append(chunk)
        
        logger.info(f"Split text of {len(text)} chars into {len(result)} chunks")
        return result
    
    def _process_claude_json(self, content: Union[str, Dict]) -> Dict[str, Any]:
        """
        Process Claude-specific JSON formats.
        
        Args:
            content: JSON content as string or parsed dict
            
        Returns:
            Processed transcript data
        """
        # Parse if string
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude JSON: {str(e)}")
                return {"text": content, "source": "claude", "error": str(e)}
        else:
            data = content
            
        # Initialize transcript
        transcript = {"source": "claude"}
        
        # Various Claude JSON formats
        if isinstance(data, list):
            # Handle list format (conversations.json)
            messages = []
            
            for item in data:
                if isinstance(item, dict):
                    # Try to extract conversation data
                    if "uuid" in item and "name" in item:
                        transcript["conversation_id"] = item.get("uuid")
                        transcript["title"] = item.get("name")
                    
                    # Extract messages if present
                    if "chat_messages" in item and isinstance(item["chat_messages"], list):
                        for msg in item["chat_messages"]:
                            if "text" in msg:
                                role = "assistant" if msg.get("assistant", False) else "user"
                                messages.append({"role": role, "content": msg["text"]})
            
            if messages:
                transcript["messages"] = messages
                transcript["text"] = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                
        elif isinstance(data, dict):
            # Handle dictionary format
            messages = []
            
            # Try to extract metadata
            if "uuid" in data:
                transcript["conversation_id"] = data["uuid"]
            if "name" in data:
                transcript["title"] = data["name"]
                
            # Extract messages
            if "chat_messages" in data and isinstance(data["chat_messages"], list):
                for msg in data["chat_messages"]:
                    if "text" in msg:
                        role = "assistant" if msg.get("assistant", False) else "user"
                        messages.append({"role": role, "content": msg["text"]})
            
            if messages:
                transcript["messages"] = messages
                transcript["text"] = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            elif "text" in data:
                # Direct text field
                transcript["text"] = data["text"]
                transcript["messages"] = [{"role": "unknown", "content": data["text"]}]
        
        # Ensure text field is present
        if "text" not in transcript or not transcript["text"]:
            # Try to extract any text content as fallback
            text_content = self._extract_text_from_data(data)
            if text_content:
                transcript["text"] = text_content
                transcript["messages"] = [{"role": "unknown", "content": text_content}]
            else:
                logger.warning("Failed to extract text from Claude JSON")
                transcript["text"] = str(data)
                transcript["messages"] = [{"role": "unknown", "content": str(data)}]
                
        # Add timestamp if missing
        if "timestamp" not in transcript:
            transcript["timestamp"] = time.time()
            
        return transcript
    
    def _process_chatgpt_json(self, content: Union[str, Dict]) -> Dict[str, Any]:
        """
        Process ChatGPT-specific JSON formats.
        
        Args:
            content: JSON content as string or parsed dict
            
        Returns:
            Processed transcript data
        """
        # Parse if string
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse ChatGPT JSON: {str(e)}")
                return {"text": content, "source": "chatgpt", "error": str(e)}
        else:
            data = content
            
        # Initialize transcript
        transcript = {"source": "chatgpt"}
        
        # Process based on ChatGPT's various formats
        if isinstance(data, list):
            # List of message objects
            messages = []
            
            for item in data:
                if isinstance(item, dict):
                    # Direct message format
                    if "role" in item and "content" in item:
                        messages.append({"role": item["role"], "content": item["content"]})
                    # Nested message format
                    elif "message" in item and isinstance(item["message"], dict):
                        msg = item["message"]
                        if "role" in msg and "content" in msg:
                            messages.append({"role": msg["role"], "content": msg["content"]})
            
            if messages:
                transcript["messages"] = messages
                transcript["text"] = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                
        elif isinstance(data, dict):
            messages = []
            
            # Try to extract metadata
            if "id" in data:
                transcript["conversation_id"] = data["id"]
            if "title" in data:
                transcript["title"] = data["title"]
            if "create_time" in data:
                transcript["timestamp"] = data["create_time"]
                
            # Handle mapping structure (common in ChatGPT exports)
            if "mapping" in data and isinstance(data["mapping"], dict):
                # First find the root
                root_node = None
                for node_id, node in data["mapping"].items():
                    if node.get("parent") == "client-created-root":
                        root_node = node
                        break
                
                # If found, traverse the conversation tree
                if root_node:
                    current_node = root_node
                    while current_node:
                        if "message" in current_node and current_node["message"]:
                            msg = current_node["message"]
                            if "author" in msg and "content" in msg:
                                role = msg["author"].get("role", "unknown")
                                
                                # Content might be structured differently
                                content = ""
                                if isinstance(msg["content"], dict) and "parts" in msg["content"]:
                                    # It's structured content
                                    parts = msg["content"]["parts"]
                                    if parts and isinstance(parts, list):
                                        content = "\n".join([str(p) for p in parts if p])
                                elif isinstance(msg["content"], str):
                                    # Simple string content
                                    content = msg["content"]
                                    
                                if content:
                                    messages.append({"role": role, "content": content})
                        
                        # Move to next node if available
                        children = current_node.get("children", [])
                        current_node = data["mapping"].get(children[0]) if children else None
            
            # Check for direct messages list
            elif "messages" in data and isinstance(data["messages"], list):
                for msg in data["messages"]:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append({"role": msg["role"], "content": msg["content"]})
            
            if messages:
                transcript["messages"] = messages
                transcript["text"] = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        # Ensure text field is present
        if "text" not in transcript or not transcript["text"]:
            # Try to extract any text content as fallback
            text_content = self._extract_text_from_data(data)
            if text_content:
                transcript["text"] = text_content
                transcript["messages"] = [{"role": "unknown", "content": text_content}]
            else:
                logger.warning("Failed to extract text from ChatGPT JSON")
                transcript["text"] = str(data)
                transcript["messages"] = [{"role": "unknown", "content": str(data)}]
                
        # Add timestamp if missing
        if "timestamp" not in transcript:
            transcript["timestamp"] = time.time()
            
        return transcript
    
    def _extract_text_from_data(self, data: Any) -> str:
        """
        Recursively extract text content from nested data structures.
        
        Args:
            data: Any data structure (dict, list, etc.)
            
        Returns:
            Extracted text
        """
        extracted_text = []
        
        if isinstance(data, dict):
            # Look for likely text fields
            for key, value in data.items():
                if key in ["text", "content", "message", "body", "transcript"]:
                    if isinstance(value, str) and len(value) > 5:
                        extracted_text.append(value)
                elif isinstance(value, (dict, list)):
                    # Recurse into nested structures
                    nested_text = self._extract_text_from_data(value)
                    if nested_text:
                        extracted_text.append(nested_text)
        
        elif isinstance(data, list):
            # Process list items
            for item in data:
                if isinstance(item, str) and len(item) > 5:
                    extracted_text.append(item)
                elif isinstance(item, (dict, list)):
                    nested_text = self._extract_text_from_data(item)
                    if nested_text:
                        extracted_text.append(nested_text)
        
        return "\n\n".join(extracted_text)
    
    def _process_text_transcript(self, content: str, source: str) -> Dict[str, Any]:
        """
        Process plain text transcripts.
        
        Args:
            content: Text content
            source: Source of the transcript
            
        Returns:
            Processed transcript data
        """
        transcript = {"text": content, "source": source, "timestamp": time.time()}
        
        # Try to parse conversation structure
        messages = []
        
        # Look for turn-taking patterns
        turn_patterns = [
            # Common messaging patterns
            (r"(?i)(Human|User|Jesse):\s*(.*?)(?=\n+(?:Claude|Assistant|AI|Grok|Gemini|ChatGPT):|$)", "user"),
            (r"(?i)(Claude|Assistant|AI):\s*(.*?)(?=\n+(?:Human|User|Jesse):|$)", "assistant"),
            (r"(?i)(Grok):\s*(.*?)(?=\n+(?:Human|User|Jesse):|$)", "assistant"),
            (r"(?i)(Gemini):\s*(.*?)(?=\n+(?:Human|User|Jesse):|$)", "assistant"),
            (r"(?i)(ChatGPT):\s*(.*?)(?=\n+(?:Human|User|Jesse):|$)", "assistant"),
        ]
        
        for pattern, role in turn_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                # match[0] is the speaker, match[1] is the content
                messages.append({"role": role, "content": match[1].strip()})
        
        # Sort messages by their position in the text
        if messages:
            # Create tuples of (position, message)
            positioned_messages = []
            for msg in messages:
                # Find where this message appears in the content
                speaker_prefix = f"{msg['role']}:" if msg['role'] in ['user', 'assistant'] else None
                if speaker_prefix:
                    pos = content.find(f"{speaker_prefix} {msg['content']}")
                    if pos >= 0:
                        positioned_messages.append((pos, msg))
            
            # Sort by position and extract just the messages
            messages = [msg for _, msg in sorted(positioned_messages, key=lambda x: x[0])]
            
            transcript["messages"] = messages
        else:
            # No structured messages found, treat as single message
            transcript["messages"] = [{"role": "unknown", "content": content}]
            
        return transcript
    
    def process_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Process a transcript file from any source.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Processed transcript data
        """
        # Determine source and type
        source = "unknown"
        file_lower = file_path.lower()
        
        # Identify source from path
        if "claude" in file_lower:
            source = "claude"
        elif "chatgpt" in file_lower or "openai" in file_lower:
            source = "chatgpt"
        elif "grok" in file_lower:
            source = "grok"
        elif "gemini" in file_lower:
            source = "gemini"
            
        # Read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if it's empty
            if not content.strip():
                logger.warning(f"Empty file: {file_path}")
                return {"text": "", "source": source, "error": "Empty file"}
                
            # Process based on file type
            if file_path.endswith('.json'):
                if source == "claude":
                    return self._process_claude_json(content)
                elif source == "chatgpt":
                    return self._process_chatgpt_json(content)
                else:
                    # Try to determine from content
                    try:
                        data = json.loads(content)
                        if any(key in data for key in ["chat_messages", "uuid"]):
                            # Likely Claude format
                            return self._process_claude_json(data)
                        elif any(key in data for key in ["mapping", "title", "create_time"]):
                            # Likely ChatGPT format
                            return self._process_chatgpt_json(data)
                        else:
                            # Generic JSON, try both formats
                            claude_result = self._process_claude_json(data)
                            if "error" not in claude_result and claude_result.get("text"):
                                return claude_result
                                
                            chatgpt_result = self._process_chatgpt_json(data)
                            if "error" not in chatgpt_result and chatgpt_result.get("text"):
                                return chatgpt_result
                                
                            # Fallback to text processing
                            return self._process_text_transcript(json.dumps(data, indent=2), source)
                    except Exception as e:
                        logger.error(f"Failed to process JSON: {str(e)}")
                        return self._process_text_transcript(content, source)
            else:
                # Text file
                return self._process_text_transcript(content, source)
                
        except Exception as e:
            logger.error(f"Failed to process transcript {file_path}: {str(e)}")
            return {"text": "", "source": source, "error": str(e)}
    
    def extract_patterns(self, transcript: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract patterns from a transcript.
        
        Args:
            transcript: Transcript data
            
        Returns:
            Dictionary of patterns by type
        """
        # Extract the text
        text = transcript.get("text", "")
        source = transcript.get("source", "unknown")
        
        if not text:
            logger.warning(f"Empty text in transcript from {source}")
            return {"error": "Empty text"}
            
        # Split text into manageable chunks if needed
        chunks = self._split_text_into_chunks(text)
        
        # Process each chunk
        all_patterns = defaultdict(list)
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} from {source}")
            
            # This is where you would call your existing pattern extraction logic
            # For now, we'll just add a placeholder
            chunk_patterns = self._placeholder_pattern_extraction(chunk, source)
            
            # Merge patterns
            for pattern_type, patterns in chunk_patterns.items():
                all_patterns[pattern_type].extend(patterns)
        
        # Remove duplicates
        for pattern_type in all_patterns:
            unique_patterns = {}
            for pattern in all_patterns[pattern_type]:
                # Create a hash of the text for deduplication
                text_hash = hashlib.md5(pattern["text"].encode()).hexdigest()
                if text_hash not in unique_patterns:
                    unique_patterns[text_hash] = pattern
            
            all_patterns[pattern_type] = list(unique_patterns.values())
            
        return dict(all_patterns)
    
    def _placeholder_pattern_extraction(self, text: str, source: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Placeholder for pattern extraction logic.
        Replace with your actual implementation.
        
        Args:
            text: Text to process
            source: Source of the text
            
        Returns:
            Dictionary of patterns by type
        """
        # This is where you would connect to your existing pattern extraction logic
        # For demonstration, we'll return a simple pattern
        patterns = {
            "Implementation_Requirements": [
                {
                    "text": "The system should prioritize privacy and security",
                    "source": source,
                    "confidence": 0.8,
                    "signal_word": "should"
                }
            ],
            "Core_Principles": [
                {
                    "text": "Trust is the foundation of human-AI collaboration",
                    "source": source,
                    "confidence": 0.9,
                    "signal_word": "trust"
                }
            ]
        }
        
        return patterns

# Example usage
if __name__ == "__main__":
    processor = EnhancedTranscriptProcessor()
    
    # Example paths
    claude_json_path = "path/to/claude/transcript.json"
    chatgpt_json_path = "path/to/chatgpt/transcript.json"
    text_path = "path/to/text/transcript.txt"
    
    # Process transcripts
    if os.path.exists(claude_json_path):
        claude_transcript = processor.process_transcript(claude_json_path)
        print(f"Processed Claude transcript: {len(claude_transcript.get('text', ''))} chars")
        
        patterns = processor.extract_patterns(claude_transcript)
        print(f"Extracted patterns: {sum(len(p) for p in patterns.values())}")
