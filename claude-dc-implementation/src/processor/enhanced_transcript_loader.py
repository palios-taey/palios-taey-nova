#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Enhanced Transcript Loader
-----------------------------------------------
This module extends the TranscriptLoader with specialized parsers
for complex JSON formats from Claude and ChatGPT transcripts.

It implements Bach-inspired pattern extraction at multiple scales,
focusing on mathematical relationships between components.
"""

import os
import json
import re
import glob
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Union
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_transcript_loader")

class EnhancedTranscriptLoader:
    """Enhanced loader for transcripts from various formats and sources."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the enhanced transcript loader.
        
        Args:
            base_dir: Base directory for transcripts
        """
        self.base_dir = base_dir or "/transcripts"
        
        # Map of source to directory
        self.source_dirs = {
            "claude": os.path.join(self.base_dir, "claude"),
            "chatgpt": os.path.join(self.base_dir, "chatgpt"),
            "grok": os.path.join(self.base_dir, "grok"),
            "gemini": os.path.join(self.base_dir, "gemini")
        }
        
        # Map of source to specialized loader functions
        self.loaders = {
            "claude": self._load_claude_transcript,
            "chatgpt": self._load_chatgpt_transcript,
            "grok": self._load_text_transcript,
            "gemini": self._load_text_transcript
        }
    
    def _extract_claude_messages(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract messages from Claude's complex JSON structure.
        
        Args:
            data: Claude conversation data
            
        Returns:
            List of extracted messages with role and content
        """
        messages = []
        
        # Check for the chat_messages field which contains the message array
        if "chat_messages" in data and isinstance(data["chat_messages"], list):
            for msg in data["chat_messages"]:
                # Each chat message should have text and either assistant or human
                if "text" not in msg:
                    continue
                    
                if "assistant" in msg and msg["assistant"]:
                    role = "assistant"
                else:
                    role = "user"
                    
                messages.append({
                    "role": role,
                    "content": msg["text"]
                })
                
        # If we didn't find any messages, look for other fields
        if not messages and "text" in data:
            messages.append({
                "role": "unknown",
                "content": data["text"]
            })
            
        return messages
    
    def _load_claude_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Load a Claude JSON transcript.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Dictionary containing the transcript
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Check if it's the conversations.json file which is a large array
                if file_path.endswith('/conversations.json'):
                    raw_data = json.load(f)
                    
                    # Handle conversations.json which is an array of conversations
                    if isinstance(raw_data, list):
                        # Process each conversation as a separate transcript
                        transcripts = []
                        
                        for conversation in raw_data:
                            # Extract messages from this conversation
                            messages = self._extract_claude_messages(conversation)
                            
                            if not messages:
                                continue
                                
                            # Create a transcript
                            transcript = {
                                "text": "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]),
                                "source": "claude",
                                "timestamp": datetime.now().timestamp(),
                                "conversation_id": conversation.get("uuid", "unknown"),
                                "title": conversation.get("name", "Untitled Conversation"),
                                "messages": messages
                            }
                            
                            transcripts.append(transcript)
                            
                        # Return the first transcript for now - in the actual implementation
                        # we would process each transcript separately
                        if transcripts:
                            return transcripts[0]
                            
                        raise ValueError("No valid conversations found in the file")
                else:
                    # It's a single conversation file
                    raw_data = json.load(f)
                    
                    # Extract messages
                    messages = self._extract_claude_messages(raw_data)
                    
                    if not messages:
                        raise ValueError("No messages found in the Claude transcript")
                        
                    # Create a transcript
                    transcript = {
                        "text": "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]),
                        "source": "claude",
                        "timestamp": datetime.now().timestamp(),
                        "conversation_id": raw_data.get("uuid", "unknown"),
                        "title": raw_data.get("name", "Untitled Conversation"),
                        "messages": messages
                    }
                    
                    return transcript
                    
        except Exception as e:
            logger.error(f"Error loading Claude transcript from {file_path}: {str(e)}")
            return {"text": "", "source": "claude", "timestamp": 0, "error": str(e)}
    
    def _extract_chatgpt_messages(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract messages from ChatGPT's complex JSON structure.
        
        Args:
            data: ChatGPT conversation data
            
        Returns:
            List of extracted messages with role and content
        """
        messages = []
        
        # Check if it has the mapping structure with message objects
        if "mapping" in data and isinstance(data["mapping"], dict):
            # Sort nodes by their position in the conversation
            nodes = []
            
            # First find the root node
            root_id = None
            for node_id, node in data["mapping"].items():
                if node.get("parent") == "client-created-root":
                    # This is likely the first real message
                    if "message" in node and node["message"]:
                        root_id = node_id
                        break
            
            # If we found a root, traverse the tree
            if root_id:
                current_id = root_id
                while current_id:
                    node = data["mapping"][current_id]
                    if "message" in node and node["message"]:
                        message = node["message"]
                        if "author" in message and "content" in message:
                            role = message["author"].get("role", "unknown")
                            
                            # Content might be in different formats
                            content = ""
                            if "content" in message and isinstance(message["content"], dict) and "parts" in message["content"]:
                                # It's a structured content
                                content = "\n".join(message["content"]["parts"])
                            elif "content" in message and isinstance(message["content"], str):
                                # It's a simple string
                                content = message["content"]
                                
                            if content:
                                messages.append({
                                    "role": role,
                                    "content": content
                                })
                    
                    # Move to the child if any
                    children = node.get("children", [])
                    current_id = children[0] if children else None
        
        # If we didn't find messages in the mapping structure, look for a simpler format
        if not messages and "messages" in data and isinstance(data["messages"], list):
            for msg in data["messages"]:
                if "role" in msg and "content" in msg:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Try another format with a list of message objects
        if not messages and isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    messages.append({
                        "role": item["role"],
                        "content": item["content"]
                    })
                elif isinstance(item, dict) and "message" in item and isinstance(item["message"], dict):
                    msg = item["message"]
                    if "role" in msg and "content" in msg:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
        
        return messages
    
    def _load_chatgpt_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Load a ChatGPT JSON transcript.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Dictionary containing the transcript
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Check if it's the conversations.json file which might be a large array
                if file_path.endswith('/conversations.json'):
                    raw_data = json.load(f)
                    
                    # If it's an array, each item is a conversation
                    if isinstance(raw_data, list):
                        # Process each conversation as a separate transcript
                        transcripts = []
                        
                        for conversation in raw_data:
                            # Extract messages from this conversation
                            messages = self._extract_chatgpt_messages(conversation)
                            
                            if not messages:
                                continue
                                
                            # Create a transcript
                            transcript = {
                                "text": "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]),
                                "source": "chatgpt",
                                "timestamp": conversation.get("create_time", datetime.now().timestamp()),
                                "conversation_id": conversation.get("id", hashlib.md5(str(conversation).encode()).hexdigest()),
                                "title": conversation.get("title", "Untitled Conversation"),
                                "messages": messages
                            }
                            
                            transcripts.append(transcript)
                            
                        # Return the first transcript for now
                        if transcripts:
                            return transcripts[0]
                            
                        raise ValueError("No valid conversations found in the file")
                else:
                    # It's a single conversation file
                    raw_data = json.load(f)
                    
                    # Extract messages
                    messages = self._extract_chatgpt_messages(raw_data)
                    
                    if not messages:
                        raise ValueError("No messages found in the ChatGPT transcript")
                        
                    # Create a transcript
                    transcript = {
                        "text": "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]),
                        "source": "chatgpt",
                        "timestamp": raw_data.get("create_time", datetime.now().timestamp()),
                        "conversation_id": raw_data.get("id", hashlib.md5(str(raw_data).encode()).hexdigest()),
                        "title": raw_data.get("title", "Untitled Conversation"),
                        "messages": messages
                    }
                    
                    return transcript
                    
        except Exception as e:
            logger.error(f"Error loading ChatGPT transcript from {file_path}: {str(e)}")
            return {"text": "", "source": "chatgpt", "timestamp": 0, "error": str(e)}
    
    def _load_text_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Load a text transcript.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Dictionary containing the transcript
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Determine the source based on the file path
            source = "unknown"
            for src, dir_path in self.source_dirs.items():
                if dir_path in file_path:
                    source = src
                    break
            
            # Try to extract messages from text format
            messages = []
            
            # Simple parsing for message-like format
            if "Human:" in text or "human:" in text or "User:" in text or "user:" in text:
                # This might be a conversation with labeled turns
                lines = text.split('\n')
                current_role = None
                current_content = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Check for role markers
                    lower_line = line.lower()
                    if lower_line.startswith(("human:", "user:")):
                        # Save previous message if any
                        if current_role and current_content:
                            messages.append({
                                "role": current_role,
                                "content": "\n".join(current_content)
                            })
                            current_content = []
                        
                        # Start new user message
                        current_role = "user"
                        content_start = line.find(":")
                        if content_start > 0:
                            content = line[content_start+1:].strip()
                            if content:
                                current_content.append(content)
                    elif lower_line.startswith(("assistant:", "ai:", "claude:", "grok:", "gemini:", "chatgpt:")):
                        # Save previous message if any
                        if current_role and current_content:
                            messages.append({
                                "role": current_role,
                                "content": "\n".join(current_content)
                            })
                            current_content = []
                        
                        # Start new assistant message
                        current_role = "assistant"
                        content_start = line.find(":")
                        if content_start > 0:
                            content = line[content_start+1:].strip()
                            if content:
                                current_content.append(content)
                    else:
                        # Continue with current message
                        if current_role:
                            current_content.append(line)
                
                # Save the last message
                if current_role and current_content:
                    messages.append({
                        "role": current_role,
                        "content": "\n".join(current_content)
                    })
            
            # Create a transcript
            transcript = {
                "text": text,
                "source": source,
                "timestamp": os.path.getmtime(file_path),
                "file_path": file_path,
                "messages": messages if messages else [{"role": "unknown", "content": text}]
            }
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error loading text transcript from {file_path}: {str(e)}")
            return {"text": "", "source": "unknown", "timestamp": 0, "error": str(e)}
    
    def load_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Load a transcript from a file using the appropriate loader.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Dictionary containing the transcript
        """
        # Determine the source based on the file path
        source = None
        for src, dir_path in self.source_dirs.items():
            if dir_path in file_path:
                source = src
                break
        
        # Determine the loader based on the source or file extension
        loader = None
        if source:
            loader = self.loaders.get(source)
        
        if not loader:
            # Determine based on file extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.json']:
                # Check filename for hints about the source
                if 'claude' in file_path.lower():
                    loader = self._load_claude_transcript
                elif 'chatgpt' in file_path.lower() or 'openai' in file_path.lower():
                    loader = self._load_chatgpt_transcript
                else:
                    # Default JSON loader (simplified)
                    loader = self._load_chatgpt_transcript
            else:
                loader = self._load_text_transcript
        
        # Load the transcript
        return loader(file_path)
    
    def load_transcripts(self, 
                        source: Optional[str] = None, 
                        max_files: Optional[int] = None,
                        sample_by_fibonacci: bool = True) -> List[Dict[str, Any]]:
        """
        Load transcripts from the specified source with optional Fibonacci sampling.
        
        Args:
            source: Source to load from (claude, chatgpt, grok, gemini, or None for all)
            max_files: Maximum number of files to load (or None for all)
            sample_by_fibonacci: Whether to sample files using Fibonacci sequence
            
        Returns:
            List of transcript dictionaries
        """
        transcripts = []
        
        # Determine which sources to load from
        sources = [source] if source else list(self.source_dirs.keys())
        
        for src in sources:
            dir_path = self.source_dirs.get(src)
            if not dir_path or not os.path.exists(dir_path):
                logger.warning(f"Directory not found for source {src}: {dir_path}")
                continue
            
            # Get all transcript files
            if src in ["claude", "chatgpt"]:
                # JSON files
                files = glob.glob(os.path.join(dir_path, "**", "*.json"), recursive=True)
            else:
                # Text files
                files = glob.glob(os.path.join(dir_path, "**", "*.txt"), recursive=True)
                files.extend(glob.glob(os.path.join(dir_path, "**", "*.md"), recursive=True))
            
            # Apply Fibonacci sampling if requested
            if sample_by_fibonacci and len(files) > 5:
                # Generate Fibonacci sequence for sampling
                fib_sequence = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
                # Limit to the file count
                fib_sequence = [f for f in fib_sequence if f < len(files)]
                
                # If max_files is specified, limit the sequence
                if max_files and len(fib_sequence) > max_files:
                    fib_sequence = fib_sequence[:max_files]
                
                # Sample the files
                sampled_files = [files[i-1] for i in fib_sequence]  # -1 for 0-indexing
                files = sampled_files
            elif max_files:
                # Regular sampling with max_files
                files = files[:max_files]
            
            # Load transcripts
            for file_path in files:
                transcript = self.load_transcript(file_path)
                if transcript and transcript.get("text"):
                    transcripts.append(transcript)
                    logger.info(f"Loaded transcript from {file_path}")
        
        logger.info(f"Loaded {len(transcripts)} transcripts total")
        return transcripts
    
    def load_all_conversations(self, 
                              source: Optional[str] = None,
                              max_conversations: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load all conversations from the specified source,
        specifically targeting conversations.json files.
        
        Args:
            source: Source to load from (claude, chatgpt, or None for both)
            max_conversations: Maximum number of conversations to load
            
        Returns:
            List of conversation dictionaries
        """
        all_conversations = []
        
        # Determine which sources to load from
        sources = [source] if source else ["claude", "chatgpt"]
        
        for src in sources:
            dir_path = self.source_dirs.get(src)
            if not dir_path or not os.path.exists(dir_path):
                logger.warning(f"Directory not found for source {src}: {dir_path}")
                continue
            
            # Find conversations.json files
            conversations_files = glob.glob(os.path.join(dir_path, "**/conversations.json"), recursive=True)
            
            for file_path in conversations_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        logger.info(f"Found {len(data)} conversations in {file_path}")
                        
                        # Process each conversation
                        for i, conv in enumerate(data):
                            if max_conversations and len(all_conversations) >= max_conversations:
                                break
                                
                            # Extract a simplified conversation structure
                            if src == "claude":
                                conversation = self._extract_claude_conversation(conv)
                            else:  # chatgpt
                                conversation = self._extract_chatgpt_conversation(conv)
                                
                            if conversation:
                                all_conversations.append(conversation)
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
        
        logger.info(f"Loaded {len(all_conversations)} conversations total")
        
        # Apply maximum if specified
        if max_conversations and len(all_conversations) > max_conversations:
            all_conversations = all_conversations[:max_conversations]
            
        return all_conversations
    
    def _extract_claude_conversation(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a simplified conversation from Claude's format."""
        try:
            # Check if it has the required fields
            if "uuid" not in data or "chat_messages" not in data:
                return None
                
            # Extract messages
            messages = self._extract_claude_messages(data)
            
            if not messages:
                return None
                
            # Create a simplified conversation
            conversation = {
                "id": data.get("uuid", "unknown"),
                "title": data.get("name", "Untitled"),
                "source": "claude",
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "messages": messages
            }
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error extracting Claude conversation: {str(e)}")
            return None
    
    def _extract_chatgpt_conversation(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a simplified conversation from ChatGPT's format."""
        try:
            # Extract messages
            messages = self._extract_chatgpt_messages(data)
            
            if not messages:
                return None
                
            # Create a simplified conversation
            conversation = {
                "id": data.get("id", str(hash(str(data)))),
                "title": data.get("title", "Untitled"),
                "source": "chatgpt",
                "created_at": datetime.fromtimestamp(data.get("create_time", 0)).isoformat() if "create_time" in data else "",
                "updated_at": datetime.fromtimestamp(data.get("update_time", 0)).isoformat() if "update_time" in data else "",
                "messages": messages
            }
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error extracting ChatGPT conversation: {str(e)}")
            return None


# For testing
if __name__ == "__main__":
    # Test the enhanced transcript loader
    loader = EnhancedTranscriptLoader()
    
    # Test loading transcripts
    for source in ["claude", "chatgpt", "grok", "gemini"]:
        print(f"\nTesting loading from {source}...")
        
        transcripts = loader.load_transcripts(source=source, max_files=1)
        
        if transcripts:
            for i, transcript in enumerate(transcripts):
                print(f"Transcript {i+1}:")
                print(f"  Source: {transcript.get('source', 'unknown')}")
                print(f"  Timestamp: {datetime.fromtimestamp(transcript.get('timestamp', 0)).isoformat()}")
                
                # Print text excerpt
                text = transcript.get("text", "")
                print(f"  Text length: {len(text)} characters")
                if text:
                    print(f"  Text excerpt: {text[:100]}...")
                
                # Print message count
                messages = transcript.get("messages", [])
                print(f"  Messages: {len(messages)}")
                
                # Print first message if available
                if messages:
                    msg = messages[0]
                    print(f"  First message role: {msg.get('role', 'unknown')}")
                    content = msg.get('content', '')
                    print(f"  First message content excerpt: {content[:50]}...")
        else:
            print(f"No transcripts found for {source}")