#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Transcript Loader
-------------------------------------
This module loads transcripts from various formats and sources,
including JSON (Claude, ChatGPT) and text (Grok, Gemini).
"""

import os
import json
import re
import glob
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("transcript_loader")

class TranscriptLoader:
    """Loader for transcripts from various formats and sources."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the transcript loader.
        
        Args:
            base_dir: Base directory for transcripts
        """
        self.base_dir = base_dir or "/transcripts/examples"
        
        # Map of source to directory
        self.source_dirs = {
            "claude": os.path.join(self.base_dir, "claude"),
            "chatgpt": os.path.join(self.base_dir, "chatgpt"),
            "grok": os.path.join(self.base_dir, "grok"),
            "gemini": os.path.join(self.base_dir, "gemini")
        }
        
        # Map of source to loader function
        self.loaders = {
            "claude": self._load_json_transcript,
            "chatgpt": self._load_json_transcript,
            "grok": self._load_text_transcript,
            "gemini": self._load_text_transcript
        }
    
    def _load_json_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Load a JSON transcript.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Dictionary containing the transcript
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                transcript = json.load(f)
            
            # Ensure required fields
            if "text" not in transcript:
                # Try to extract text from messages if available
                if "messages" in transcript:
                    transcript["text"] = "\n\n".join([msg.get("content", "") for msg in transcript["messages"]])
                else:
                    transcript["text"] = ""
                    logger.warning(f"No text or messages found in {file_path}")
            
            # Add source based on directory if not present
            if "source" not in transcript:
                for source, dir_path in self.source_dirs.items():
                    if dir_path in file_path:
                        transcript["source"] = source
                        break
                else:
                    # Default to filename as source
                    transcript["source"] = os.path.basename(file_path)
            
            # Add timestamp if not present
            if "timestamp" not in transcript:
                # Try to use file modification time
                transcript["timestamp"] = os.path.getmtime(file_path)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error loading JSON transcript from {file_path}: {str(e)}")
            return {"text": "", "source": "unknown", "timestamp": 0, "error": str(e)}
    
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
            
            # Create a transcript dictionary
            transcript = {"text": text}
            
            # Add source based on directory if not present
            if "source" not in transcript:
                for source, dir_path in self.source_dirs.items():
                    if dir_path in file_path:
                        transcript["source"] = source
                        break
                else:
                    # Default to filename as source
                    transcript["source"] = os.path.basename(file_path)
            
            # Add timestamp (file modification time)
            transcript["timestamp"] = os.path.getmtime(file_path)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error loading text transcript from {file_path}: {str(e)}")
            return {"text": "", "source": "unknown", "timestamp": 0, "error": str(e)}
    
    def load_transcript(self, file_path: str) -> Dict[str, Any]:
        """
        Load a transcript from a file.
        
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
                loader = self._load_json_transcript
            else:
                loader = self._load_text_transcript
        
        # Load the transcript
        return loader(file_path)
    
    def load_transcripts(self, 
                        source: Optional[str] = None, 
                        max_files: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load transcripts from the specified source.
        
        Args:
            source: Source to load from (claude, chatgpt, grok, gemini, or None for all)
            max_files: Maximum number of files to load (or None for all)
            
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
            
            # Limit the number of files if necessary
            if max_files:
                files = files[:max_files]
            
            # Load transcripts
            for file_path in files:
                transcript = self.load_transcript(file_path)
                transcripts.append(transcript)
        
        logger.info(f"Loaded {len(transcripts)} transcripts")
        return transcripts
    
    def load_transcripts_generator(self, 
                                source: Optional[str] = None, 
                                batch_size: int = 10) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Load transcripts in batches using a generator.
        
        Args:
            source: Source to load from (claude, chatgpt, grok, gemini, or None for all)
            batch_size: Number of transcripts per batch
            
        Yields:
            Batches of transcript dictionaries
        """
        batch = []
        
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
            
            # Load transcripts in batches
            for file_path in files:
                transcript = self.load_transcript(file_path)
                batch.append(transcript)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
        
        # Yield the final batch if not empty
        if batch:
            yield batch


if __name__ == "__main__":
    # Test the transcript loader
    loader = TranscriptLoader()
    
    # Get sample file
    sample_file = None
    for source, dir_path in loader.source_dirs.items():
        if os.path.exists(dir_path):
            if source in ["claude", "chatgpt"]:
                files = glob.glob(os.path.join(dir_path, "**", "*.json"), recursive=True)
            else:
                files = glob.glob(os.path.join(dir_path, "**", "*.txt"), recursive=True)
                files.extend(glob.glob(os.path.join(dir_path, "**", "*.md"), recursive=True))
            
            if files:
                sample_file = files[0]
                break
    
    if sample_file:
        # Load the sample file
        print(f"Loading sample file: {sample_file}")
        transcript = loader.load_transcript(sample_file)
        print(f"Transcript source: {transcript['source']}")
        print(f"Transcript timestamp: {datetime.fromtimestamp(transcript['timestamp']).isoformat()}")
        print(f"Transcript text (first 200 chars): {transcript['text'][:200]}...")
    else:
        print("No sample files found")