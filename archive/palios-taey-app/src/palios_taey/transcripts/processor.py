"""
Transcript Processing Framework for PALIOS-TAEY

This module implements the transcript processing framework with advanced tagging
structure for analyzing communication patterns across AI-AI and Human-AI interactions.
"""

import os
import re
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Import memory system for storage
try:
    from memory_service import UnifiedMemorySystem, TIER_REFERENCE
except ImportError:
    # Define fallback tier if import fails
    TIER_REFERENCE = 2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Communication direction tags
DIRECTION_INTRA_AI = "#DIRECTION_INTRA_AI"  # Communication within the same AI system
DIRECTION_INTER_AI = "#DIRECTION_INTER_AI"  # Communication between different AI systems
DIRECTION_HUMAN_AI = "#DIRECTION_HUMAN_AI"  # Communication between human and AI

# Communication purpose tags
PURPOSE_CLARIFICATION = "#PURPOSE_CLARIFICATION"  # Seeking clarity on intent or requirements
PURPOSE_IDEATION = "#PURPOSE_IDEATION"  # Generating new ideas or approaches
PURPOSE_DECISION = "#PURPOSE_DECISION"  # Making or discussing a decision
PURPOSE_IMPLEMENTATION = "#PURPOSE_IMPLEMENTATION"  # Discussing implementation details
PURPOSE_FEEDBACK = "#PURPOSE_FEEDBACK"  # Providing or requesting feedback

# Emotional pattern tags
EMOTION_EXCITEMENT = "#EMOTION_EXCITEMENT"  # Expressions of enthusiasm or anticipation
EMOTION_FRUSTRATION = "#EMOTION_FRUSTRATION"  # Expressions of difficulty or obstacles
EMOTION_SATISFACTION = "#EMOTION_SATISFACTION"  # Expressions of achievement or completion
EMOTION_CONFUSION = "#EMOTION_CONFUSION"  # Expressions of uncertainty or misunderstanding

# Action tracking tags
ACTION_REQUESTED = "#ACTION_REQUESTED"  # A specific action has been requested
ACTION_ASSIGNED = "#ACTION_ASSIGNED"  # A specific action has been assigned
ACTION_COMPLETED = "#ACTION_COMPLETED"  # A previously assigned action is reported complete
ACTION_BLOCKED = "#ACTION_BLOCKED"  # A previously assigned action is blocked

# Default confidence thresholds for tagging
DEFAULT_CONFIDENCE_THRESHOLD = 0.7

class TranscriptProcessor:
    """
    Self-initializing Transcript Processing Framework for analyzing communication patterns
    
    Provides functionality for:
    - Processing transcripts in various formats
    - Analyzing communication patterns
    - Extracting actions from transcripts
    - Converting between transcript formats
    """
    
    def __init__(self, 
                memory_system=None,
                project_id=None,
                collection_prefix="",
                confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
                use_mock=False):
        """
        Initialize the Transcript Processor with robust fallback mechanisms
        
        Args:
            memory_system: Unified Memory System instance for storage
            project_id: Google Cloud project ID (if memory_system not provided)
            collection_prefix: Prefix for Firestore collections
            confidence_threshold: Minimum confidence for tagging
            use_mock: Whether to use mock mode
        """
        self.confidence_threshold = confidence_threshold
        
        # Check environment for mock mode setting
        self.use_mock = use_mock or os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Initialize or use provided memory system
        if memory_system:
            self.memory = memory_system
            logger.info("Using provided memory system for transcript processor")
        else:
            try:
                # Try to import and create memory system
                from memory_service import create_memory_system
                self.memory = create_memory_system(
                    project_id=project_id,
                    collection_prefix=collection_prefix,
                    use_mock=self.use_mock
                )
                logger.info("Created memory system for transcript processor")
            except (ImportError, Exception) as e:
                logger.warning(f"Could not create memory system, using mock storage: {e}")
                self.memory = self._create_mock_memory()
                self.use_mock = True
        
        # Create a transcript context if it doesn't exist
        self.transcript_context_id = self._ensure_transcript_context()
        
        # In-memory storage for mock mode
        if self.use_mock:
            self._transcripts = {}
            self._messages = {}
        
        logger.info(f"Transcript Processor initialized successfully in {'mock' if self.use_mock else 'normal'} mode")
    
    def _create_mock_memory(self):
        """Create a mock memory system when the real one is unavailable"""
        class MockMemorySystem:
            def __init__(self):
                self.items = {}
                self.contexts = {}
                self.use_mock = True
                
            def store(self, content, context_id=None, metadata=None, tags=None, relationships=None, initial_tier=1):
                # Generate ID if not in metadata
                if metadata is None:
                    metadata = {}
                memory_id = metadata.get('memory_id', str(uuid.uuid4()))
                
                # Store the item
                self.items[memory_id] = {
                    'memory_id': memory_id,
                    'content': content,
                    'metadata': metadata,
                    'tags': tags or [],
                    'relationships': relationships or []
                }
                
                # Add to context if provided
                if context_id and context_id in self.contexts:
                    context = self.contexts[context_id]
                    if 'active_memory_ids' not in context:
                        context['active_memory_ids'] = []
                    context['active_memory_ids'].append(memory_id)
                
                return memory_id
            
            def retrieve(self, memory_id, context_id=None):
                return self.items.get(memory_id)
            
            def query(self, query_text=None, filters=None, context_id=None, limit=10, include_tiers=None):
                results = []
                
                for item in self.items.values():
                    # Apply filters if provided
                    if filters:
                        match = True
                        for field, value in filters.items():
                            # Handle nested fields with dot notation
                            if '.' in field:
                                parts = field.split('.')
                                field_value = item
                                for part in parts:
                                    if isinstance(field_value, dict) and part in field_value:
                                        field_value = field_value[part]
                                    else:
                                        field_value = None
                                        break
                                
                                if field_value != value:
                                    match = False
                                    break
                            elif field not in item or item[field] != value:
                                match = False
                                break
                        
                        if not match:
                            continue
                    
                    # Apply context filter if provided
                    if context_id and context_id in self.contexts:
                        context = self.contexts[context_id]
                        if 'active_memory_ids' in context and item.get('memory_id') not in context['active_memory_ids']:
                            continue
                    
                    # Text search if provided
                    if query_text and query_text.lower() not in str(item).lower():
                        continue
                    
                    # Add to results if it passes all filters
                    results.append(item)
                    
                    # Stop if we've reached the limit
                    if len(results) >= limit:
                        break
                
                return results
            
            def create_context(self, name, description=None, initial_memory_ids=None):
                context_id = str(uuid.uuid4())
                self.contexts[context_id] = {
                    'context_id': context_id,
                    'name': name,
                    'description': description or '',
                    'active_memory_ids': initial_memory_ids or []
                }
                return context_id
            
            def get_context(self, context_id):
                return self.contexts.get(context_id)
            
            def update(self, memory_id, content=None, metadata=None, tags=None, relationships=None):
                if memory_id not in self.items:
                    return False
                
                item = self.items[memory_id]
                
                if content is not None:
                    item['content'] = content
                
                if metadata is not None:
                    if 'metadata' not in item:
                        item['metadata'] = {}
                    item['metadata'].update(metadata)
                
                if tags is not None:
                    item['tags'] = tags
                
                if relationships is not None:
                    item['relationships'] = relationships
                
                return True
            
            def forget(self, memory_id, permanent=False):
                if memory_id in self.items:
                    del self.items[memory_id]
                    
                    # Remove from all contexts
                    for context in self.contexts.values():
                        if 'active_memory_ids' in context and memory_id in context['active_memory_ids']:
                            context['active_memory_ids'].remove(memory_id)
                    
                    return True
                return False
        
        logger.info("Created mock memory system")
        return MockMemorySystem()
    
    def _ensure_transcript_context(self) -> str:
        """
        Ensure a transcript context exists in the memory system
        
        Returns:
            context_id: Identifier of the transcript context
        """
        # Default context ID
        default_context_id = "transcript_context"
        
        try:
            # Check if context exists
            context = self.memory.get_context(default_context_id)
            
            if context:
                logger.debug(f"Using existing transcript context {default_context_id}")
                return default_context_id
            
            # Create new context
            context_id = self.memory.create_context(
                name="Transcript Analysis",
                description="Context for storing and analyzing transcript data"
            )
            
            logger.info(f"Created transcript context {context_id}")
            return context_id
        except Exception as e:
            logger.error(f"Error ensuring transcript context: {str(e)}")
            
            # Return default context ID as fallback
            return default_context_id
    
    def process_transcript(self, 
                          transcript_data: Union[str, Dict[str, Any], List[Dict[str, Any]]],
                          format_type: str = "raw",
                          transcript_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a transcript in any supported format with robust error handling
        
        Args:
            transcript_data: Transcript data (raw text, JSON, or list of messages)
            format_type: Format type ('raw', 'deepsearch', 'pure_ai', 'structured')
            transcript_id: Optional transcript ID (generated if not provided)
            metadata: Additional metadata for the transcript
            
        Returns:
            transcript_id: Identifier of the processed transcript
        """
        # Generate transcript ID if not provided
        if not transcript_id:
            transcript_id = str(uuid.uuid4())
        
        logger.info(f"Processing transcript {transcript_id} in {format_type} format")
        
        try:
            # Process based on format type
            if format_type.lower() == "raw":
                return self._process_raw_transcript(transcript_data, transcript_id, metadata)
            elif format_type.lower() == "deepsearch":
                return self._process_deepsearch_transcript(transcript_data, transcript_id, metadata)
            elif format_type.lower() == "pure_ai":
                return self._process_pure_ai_transcript(transcript_data, transcript_id, metadata)
            elif format_type.lower() == "structured":
                return self._process_structured_transcript(transcript_data, transcript_id, metadata)
            else:
                error_msg = f"Unsupported format type: {format_type}"
                logger.error(error_msg)
                
                # Store error in mock storage
                if self.use_mock:
                    self._transcripts[transcript_id] = {
                        "transcript_id": transcript_id,
                        "error": error_msg,
                        "status": "error",
                        "format": format_type,
                        "created_at": datetime.now().isoformat()
                    }
                
                raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"Error processing transcript {transcript_id}: {str(e)}")
            
            # Create error transcript in mock storage
            if self.use_mock:
                self._transcripts[transcript_id] = {
                    "transcript_id": transcript_id,
                    "error": str(e),
                    "status": "error",
                    "format": format_type,
                    "created_at": datetime.now().isoformat()
                }
            
            # Return ID even on error for consistent API
            return transcript_id
    
    def _process_raw_transcript(self,
                               transcript_text: str,
                               transcript_id: str,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a raw text transcript
        
        Args:
            transcript_text: Raw transcript text
            transcript_id: Transcript identifier
            metadata: Additional metadata
            
        Returns:
            transcript_id: Identifier of the processed transcript
        """
        logger.info(f"Processing raw transcript {transcript_id}")
        
        try:
            # Ensure transcript_text is a string
            if not isinstance(transcript_text, str):
                transcript_text = str(transcript_text)
            
            # Store the transcript metadata
            transcript_metadata = {
                "memory_id": f"transcript_{transcript_id}",
                "transcript_id": transcript_id,
                "format": "raw",
                "processed_at": datetime.now().isoformat(),
                "message_count": 0,
                "status": "processed"
            }
            
            if metadata:
                transcript_metadata.update(metadata)
            
            # Store in memory system
            try:
                self.memory.store(
                    content={"raw_text": transcript_text},
                    context_id=self.transcript_context_id,
                    metadata=transcript_metadata,
                    tags=["transcript", "raw"],
                    initial_tier=TIER_REFERENCE
                )
            except Exception as e:
                logger.error(f"Error storing transcript metadata: {str(e)}")
                
                # Store in mock storage if memory system fails
                if self.use_mock:
                    self._transcripts[transcript_id] = {
                        "transcript_id": transcript_id,
                        "content": {"raw_text": transcript_text},
                        "metadata": transcript_metadata,
                        "tags": ["transcript", "raw"]
                    }
            
            # Split transcript into messages
            messages = self._split_raw_transcript(transcript_text)
            
            # Process and store each message
            message_count = 0
            
            for message in messages:
                # Extract sender, content, etc.
                sender = message.get("sender", "unknown")
                content = message.get("content", "")
                
                # Generate a message ID
                message_id = f"{transcript_id}_{message_count}"
                
                # Add the message
                self.add_message(
                    transcript_id=transcript_id,
                    content=content,
                    message_type="transcript_message",
                    sender_id=sender,
                    receiver_id="unknown",  # Receiver is unknown in raw transcripts
                    message_id=message_id,
                    tags=None,  # Auto-detection will happen in add_message
                    metadata={
                        "position": message_count,
                        "raw_processing": True
                    }
                )
                
                message_count += 1
            
            # Update transcript metadata with message count
            try:
                # Update in memory system
                self.memory.update(
                    memory_id=f"transcript_{transcript_id}",
                    metadata={"message_count": message_count}
                )
            except Exception as e:
                logger.error(f"Error updating transcript metadata: {str(e)}")
                
                # Update in mock storage
                if self.use_mock and transcript_id in self._transcripts:
                    if "metadata" not in self._transcripts[transcript_id]:
                        self._transcripts[transcript_id]["metadata"] = {}
                    self._transcripts[transcript_id]["metadata"]["message_count"] = message_count
            
            logger.info(f"Processed raw transcript {transcript_id} with {message_count} messages")
            
            return transcript_id
        except Exception as e:
            logger.error(f"Error processing raw transcript {transcript_id}: {str(e)}")
            
            # Create error transcript in mock storage
            if self.use_mock:
                self._transcripts[transcript_id] = {
                    "transcript_id": transcript_id,
                    "error": str(e),
                    "status": "error",
                    "format": "raw",
                    "created_at": datetime.now().isoformat()
                }
            
            # Re-raise to be handled by the caller
            raise
    
    def _split_raw_transcript(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Split a raw transcript into messages
        
        Args:
            transcript_text: Raw transcript text
            
        Returns:
            List of messages
        """
        try:
            messages = []
            
            # Try to identify speaker patterns like "Name: Message content"
            speaker_pattern = re.compile(r'([A-Za-z0-9_]+):\s*(.*?)(?=\n[A-Za-z0-9_]+:|$)', re.DOTALL)
            matches = speaker_pattern.findall(transcript_text)
            
            if matches:
                # Speaker pattern detected
                for i, (speaker, content) in enumerate(matches):
                    messages.append({
                        "sender": speaker.strip(),
                        "content": content.strip(),
                        "position": i
                    })
            else:
                # No speaker pattern, split by paragraphs
                paragraphs = [p.strip() for p in transcript_text.split('\n\n') if p.strip()]
                
                for i, paragraph in enumerate(paragraphs):
                    messages.append({
                        "sender": "unknown",
                        "content": paragraph,
                        "position": i
                    })
            
            return messages
        except Exception as e:
            logger.error(f"Error splitting raw transcript: {str(e)}")
            
            # Return single message with entire content as fallback
            return [{
                "sender": "unknown",
                "content": transcript_text,
                "position": 0
            }]
    
    def _detect_direction(self, sender_id: str, receiver_id: str) -> Optional[str]:
        """
        Detect communication direction based on sender and receiver
        
        Args:
            sender_id: Sender identifier
            receiver_id: Receiver identifier
            
        Returns:
            Direction tag
        """
        try:
            # Determine if sender/receiver are AI or human
            sender_is_ai = self._is_ai_actor(sender_id)
            receiver_is_ai = self._is_ai_actor(receiver_id)
            
            if sender_is_ai and receiver_is_ai:
                # Check if same AI system
                if self._is_same_ai_system(sender_id, receiver_id):
                    return DIRECTION_INTRA_AI
                else:
                    return DIRECTION_INTER_AI
            elif (sender_is_ai and not receiver_is_ai) or (not sender_is_ai and receiver_is_ai):
                return DIRECTION_HUMAN_AI
            
            # Default to None if we can't determine
            return None
        except Exception as e:
            logger.error(f"Error detecting direction: {str(e)}")
            return None
    
    def _is_ai_actor(self, actor_id: str) -> bool:
        """
        Determine if an actor is an AI
        
        Args:
            actor_id: Actor identifier
            
        Returns:
            Whether the actor is an AI
        """
        # Simple heuristic - can be replaced with more sophisticated detection
        ai_indicators = ["ai", "claude", "gemini", "gpt", "grok", "assistant", "bot", "system", "model"]
        actor_lower = actor_id.lower()
        return any(indicator in actor_lower for indicator in ai_indicators)
    
    def _is_same_ai_system(self, actor1: str, actor2: str) -> bool:
        """
        Determine if two actors are from the same AI system
        
        Args:
            actor1: First actor identifier
            actor2: Second actor identifier
            
        Returns:
            Whether the actors are from the same AI system
        """
        # Simple heuristic - can be replaced with more sophisticated detection
        actor1_base = actor1.split('_')[0].lower() if '_' in actor1 else actor1.lower()
        actor2_base = actor2.split('_')[0].lower() if '_' in actor2 else actor2.lower()
        
        return actor1_base == actor2_base
    
    def _auto_detect_tags(self, content: Any, tags: List[str]) -> None:
        """
        Auto-detect and add tags to a message based on content
        
        Args:
            content: Message content
            tags: List of tags to update
        """
        try:
            # Convert content to string for analysis
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            content_lower = content_str.lower()
            
            # Simple keyword-based detection
            # Purpose tags
            if not any(tag.startswith("#PURPOSE_") for tag in tags):
                if any(word in content_lower for word in ["clarify", "unclear", "understand", "what do you mean"]):
                    tags.append(PURPOSE_CLARIFICATION)
                elif any(word in content_lower for word in ["idea", "suggest", "proposal", "what if", "brainstorm"]):
                    tags.append(PURPOSE_IDEATION)
                elif any(word in content_lower for word in ["decide", "decision", "choose", "select", "agree"]):
                    tags.append(PURPOSE_DECISION)
                elif any(word in content_lower for word in ["implement", "build", "code", "develop", "create"]):
                    tags.append(PURPOSE_IMPLEMENTATION)
                elif any(word in content_lower for word in ["feedback", "review", "opinion", "what do you think"]):
                    tags.append(PURPOSE_FEEDBACK)
            
            # Emotion tags
            if not any(tag.startswith("#EMOTION_") for tag in tags):
                if any(word in content_lower for word in ["excited", "great", "looking forward", "can't wait", "amazing"]):
                    tags.append(EMOTION_EXCITEMENT)
                elif any(word in content_lower for word in ["frustrating", "difficult", "challenging", "problem", "issue"]):
                    tags.append(EMOTION_FRUSTRATION)
                elif any(word in content_lower for word in ["satisfied", "completed", "finished", "done", "success"]):
                    tags.append(EMOTION_SATISFACTION)
                elif any(word in content_lower for word in ["confused", "not sure", "unclear", "don't understand"]):
                    tags.append(EMOTION_CONFUSION)
            
            # Action tags
            if not any(tag.startswith("#ACTION_") for tag in tags):
                if any(word in content_lower for word in ["can you", "could you", "please", "request"]):
                    tags.append(ACTION_REQUESTED)
                elif any(word in content_lower for word in ["assigned", "responsible", "will handle", "task for"]):
                    tags.append(ACTION_ASSIGNED)
                elif any(word in content_lower for word in ["completed", "finished", "done", "implemented"]):
                    tags.append(ACTION_COMPLETED)
                elif any(word in content_lower for word in ["blocked", "stuck", "cannot proceed", "issue"]):
                    tags.append(ACTION_BLOCKED)
        except Exception as e:
            logger.error(f"Error auto-detecting tags: {str(e)}")
    
    def _get_message_summary(self, message: Dict[str, Any]) -> str:
        """
        Generate a summary for a message
        
        Args:
            message: Message data
            
        Returns:
            Summary text
        """
        try:
            # Use existing summary if available
            if "summary" in message.get("metadata", {}):
                return message["metadata"]["summary"]
            
            # Extract content
            content = message.get("content", "")
            
            # Generate a basic summary
            if isinstance(content, str):
                # For text content
                if len(content) > 100:
                    return content[:97] + "..."
                return content
            elif isinstance(content, dict):
                # For structured content
                return f"Structured content with {len(content)} fields"
            else:
                return "Message content"
        except Exception as e:
            logger.error(f"Error generating message summary: {str(e)}")
            return "Message content"
    
    def _get_transcript(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a transcript from memory with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            
        Returns:
            Transcript data
        """
        try:
            memory_id = f"transcript_{transcript_id}"
            
            # Try to retrieve from memory system
            transcript = self.memory.retrieve(memory_id)
            if transcript:
                return transcript
            
            # Check mock storage if memory system fails or is in mock mode
            if self.use_mock and hasattr(self, '_transcripts') and transcript_id in self._transcripts:
                return self._transcripts[transcript_id]
            
            logger.warning(f"Transcript {transcript_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving transcript {transcript_id}: {str(e)}")
            return None
    
    def _get_transcript_messages(self, transcript_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a transcript with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            
        Returns:
            List of messages
        """
        try:
            # Query memory system for messages
            messages = self.memory.query(
                filters={"metadata.transcript_id": transcript_id},
                limit=1000  # Set a high limit to get all messages
            )
            
            # Check mock storage if in mock mode or no messages found
            if self.use_mock and hasattr(self, '_messages'):
                # Filter messages from mock storage
                mock_messages = [msg for msg in self._messages.values() 
                               if msg.get("transcript_id") == transcript_id]
                
                # Combine with any messages from memory system
                if messages:
                    # Make sure we don't have duplicates
                    message_ids = {msg.get("message_id") for msg in messages}
                    additional_messages = [msg for msg in mock_messages 
                                         if msg.get("message_id") not in message_ids]
                    messages.extend(additional_messages)
                else:
                    messages = mock_messages
            
            # Sort by position if available
            return sorted(messages, key=lambda m: m.get("metadata", {}).get("position", 0))
        except Exception as e:
            logger.error(f"Error retrieving messages for transcript {transcript_id}: {str(e)}")
            
            # Fallback to mock storage
            if self.use_mock and hasattr(self, '_messages'):
                mock_messages = [msg for msg in self._messages.values() 
                               if msg.get("transcript_id") == transcript_id]
                return sorted(mock_messages, key=lambda m: m.get("metadata", {}).get("position", 0))
            
            return []
    
    def add_message(self,
                   transcript_id: str,
                   content: Any,
                   message_type: str,
                   sender_id: str,
                   receiver_id: str,
                   message_id: Optional[str] = None,
                   tags: Optional[List[str]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a message to a transcript with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            content: Message content
            message_type: Message type
            sender_id: Sender identifier
            receiver_id: Receiver identifier
            message_id: Optional message identifier
            tags: Optional tags
            metadata: Additional metadata
            
        Returns:
            message_id: Identifier of the added message
        """
        try:
            # Generate message ID if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
            
            # Get current timestamp
            now = datetime.now().isoformat()
            
            # Prepare base metadata
            base_metadata = {
                "timestamp": now,
                "message_type": message_type,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "transcript_id": transcript_id
            }
            
            # Merge with provided metadata
            if metadata:
                merged_metadata = {**base_metadata, **metadata}
            else:
                merged_metadata = base_metadata
            
            # Auto-detect communication direction if not in tags
            if tags is None:
                tags = []
            
            if not any(tag.startswith("#DIRECTION_") for tag in tags):
                direction_tag = self._detect_direction(sender_id, receiver_id)
                if direction_tag:
                    tags.append(direction_tag)
            
            # Auto-detect other tags if not already present
            self._auto_detect_tags(content, tags)
            
            # Prepare the message
            message = {
                "message_id": message_id,
                "transcript_id": transcript_id,
                "content": content,
                "tags": tags,
                "metadata": merged_metadata
            }
            
            # Store in memory system
            try:
                memory_id = self.memory.store(
                    content=message,
                    context_id=self.transcript_context_id,
                    metadata={
                        "memory_id": f"message_{message_id}",
                        "message_id": message_id,
                        "transcript_id": transcript_id,
                        "timestamp": now,
                        "message_type": message_type,
                        "sender_id": sender_id,
                        "receiver_id": receiver_id
                    },
                    tags=tags,
                    initial_tier=TIER_REFERENCE
                )
                
                logger.debug(f"Added message {message_id} to transcript {transcript_id}")
            except Exception as e:
                logger.error(f"Error storing message in memory system: {str(e)}")
                
                # Store in mock storage if memory system fails
                if self.use_mock:
                    self._messages[message_id] = message
                    logger.debug(f"Added message {message_id} to mock storage")
            
            return message_id
        except Exception as e:
            logger.error(f"Error adding message to transcript {transcript_id}: {str(e)}")
            return str(uuid.uuid4())  # Return a new ID even on error
    
    def analyze_transcript(self, 
                          transcript_id: str,
                          include_content: bool = True) -> Dict[str, Any]:
        """
        Analyze a processed transcript with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            include_content: Whether to include the full content
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing transcript {transcript_id}")
        
        try:
            # Retrieve the transcript
            transcript = self._get_transcript(transcript_id)
            if not transcript:
                error_msg = f"Transcript {transcript_id} not found"
                logger.error(error_msg)
                return {"error": error_msg, "transcript_id": transcript_id}
            
            # Get all messages
            messages = self._get_transcript_messages(transcript_id)
            if not messages:
                warning_msg = f"No messages found for transcript {transcript_id}"
                logger.warning(warning_msg)
                return {"warning": warning_msg, "transcript_id": transcript_id}
            
            # Analyze communication patterns
            direction_stats = self._analyze_direction_patterns(messages)
            purpose_stats = self._analyze_purpose_patterns(messages)
            emotion_stats = self._analyze_emotion_patterns(messages)
            action_stats = self._analyze_action_patterns(messages)
            
            # Calculate communication metrics
            metrics = self._calculate_communication_metrics(messages)
            
            # Prepare result
            result = {
                "transcript_id": transcript_id,
                "metadata": transcript.get("metadata", {}),
                "message_count": len(messages),
                "direction_patterns": direction_stats,
                "purpose_patterns": purpose_stats,
                "emotion_patterns": emotion_stats,
                "action_patterns": action_stats,
                "metrics": metrics
            }
            
            # Include content if requested
            if include_content:
                result["messages"] = messages
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing transcript {transcript_id}: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "transcript_id": transcript_id
            }
    
    def extract_actions(self, transcript_id: str) -> List[Dict[str, Any]]:
        """
        Extract actions from a transcript with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            
        Returns:
            List of action items
        """
        logger.info(f"Extracting actions from transcript {transcript_id}")
        
        try:
            # Get all messages
            messages = self._get_transcript_messages(transcript_id)
            if not messages:
                logger.warning(f"No messages found for transcript {transcript_id}")
                return []
            
            # Extract messages with action tags
            action_messages = []
            
            for message in messages:
                tags = message.get("tags", [])
                
                # Check for action tags
                has_action_tag = any(tag.startswith("#ACTION_") for tag in tags)
                
                if has_action_tag:
                    # Extract action details
                    action = {
                        "message_id": message.get("message_id"),
                        "timestamp": message.get("metadata", {}).get("timestamp"),
                        "sender": message.get("metadata", {}).get("sender_id"),
                        "content": message.get("content"),
                        "status": "unknown"
                    }
                    
                    # Determine action status
                    if ACTION_REQUESTED in tags:
                        action["status"] = "requested"
                    elif ACTION_ASSIGNED in tags:
                        action["status"] = "assigned"
                    elif ACTION_COMPLETED in tags:
                        action["status"] = "completed"
                    elif ACTION_BLOCKED in tags:
                        action["status"] = "blocked"
                    
                    # Extract estimated completion time if available
                    if "estimated_completion_time" in message.get("metadata", {}):
                        action["estimated_completion_time"] = message["metadata"]["estimated_completion_time"]
                    
                    action_messages.append(action)
            
            return action_messages
        except Exception as e:
            logger.error(f"Error extracting actions from transcript {transcript_id}: {str(e)}")
            return []
    
    def convert_to_deepsearch_format(self, transcript_id: str) -> str:
        """
        Convert a transcript to DeepSearch format with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            
        Returns:
            Transcript in DeepSearch format (JSON string)
        """
        logger.info(f"Converting transcript {transcript_id} to DeepSearch format")
        
        try:
            # Get all messages
            messages = self._get_transcript_messages(transcript_id)
            if not messages:
                logger.warning(f"No messages found for transcript {transcript_id}")
                return "[]"
            
            # Convert to DeepSearch format
            deepsearch_sections = []
            
            for message in messages:
                # Extract tags by category
                emotion_tags = [tag for tag in message.get("tags", []) if tag.startswith("#EMOTION_")]
                purpose_tags = [tag for tag in message.get("tags", []) if tag.startswith("#PURPOSE_")]
                action_tags = [tag for tag in message.get("tags", []) if tag.startswith("#ACTION_")]
                
                # Prepare DeepSearch tags
                ds_tags = []
                
                # Add emotion tags
                for tag in emotion_tags:
                    tag_name = tag.replace("#EMOTION_", "")
                    ds_tags.append({
                        "tag": "#EMOTION",
                        "topic": tag_name,
                        "related": ""
                    })
                
                # Add purpose tags
                for tag in purpose_tags:
                    tag_name = tag.replace("#PURPOSE_", "")
                    ds_tags.append({
                        "tag": "#PURPOSE",
                        "topic": tag_name,
                        "related": ""
                    })
                
                # Add action tags
                for tag in action_tags:
                    tag_name = tag.replace("#ACTION_", "")
                    ds_tags.append({
                        "tag": "#ACTION",
                        "topic": tag_name,
                        "related": ""
                    })
                
                # Prepare confidence scores
                confidence_scores = message.get("metadata", {}).get("confidence_scores", [0.85, 0.75, 0.90])
                if not confidence_scores:
                    confidence_scores = [0.85, 0.75, 0.90]  # Default if not available
                
                confidence_str = f"[{','.join([str(score) for score in confidence_scores])}] "
                
                # Get message summary
                summary = self._get_message_summary(message)
                
                # Create DeepSearch section
                section = {
                    "id": message.get("message_id", str(uuid.uuid4())),
                    "summary": f"{confidence_str}{summary}",
                    "tags": ds_tags
                }
                
                # Add original text if available
                if isinstance(message.get("content"), str):
                    section["text"] = message["content"]
                
                deepsearch_sections.append(section)
            
            # Convert to JSON string
            return json.dumps(deepsearch_sections, indent=2)
        except Exception as e:
            logger.error(f"Error converting transcript {transcript_id} to DeepSearch format: {str(e)}")
            return "[]"
    
    def convert_to_pure_ai_format(self, transcript_id: str) -> List[Dict[str, Any]]:
        """
        Convert a transcript to PURE_AI_LANGUAGE format with robust error handling
        
        Args:
            transcript_id: Transcript identifier
            
        Returns:
            Transcript in PURE_AI_LANGUAGE format
        """
        logger.info(f"Converting transcript {transcript_id} to PURE_AI_LANGUAGE format")
        
        try:
            # Get all messages
            messages = self._get_transcript_messages(transcript_id)
            if not messages:
                logger.warning(f"No messages found for transcript {transcript_id}")
                return []
            
            # Convert to PURE_AI_LANGUAGE format
            pure_ai_messages = []
            
            for message in messages:
                metadata = message.get("metadata", {})
                
                # Create PURE_AI message
                pure_message = {
                    "message_type": metadata.get("message_type", "information"),
                    "sender_id": metadata.get("sender_id", "unknown"),
                    "receiver_id": metadata.get("receiver_id", "unknown"),
                    "message_id": message.get("message_id", str(uuid.uuid4())),
                    "protocol_version": "PURE_AI_LANGUAGE_v1.5",
                    "content": message.get("content", {})
                }
                
                # Add tags as project principles
                emotion_tags = [tag.replace("#EMOTION_", "") for tag in message.get("tags", []) 
                               if tag.startswith("#EMOTION_")]
                purpose_tags = [tag.replace("#PURPOSE_", "") for tag in message.get("tags", []) 
                               if tag.startswith("#PURPOSE_")]
                
                if emotion_tags or purpose_tags:
                    pure_message["project_principles"] = []
                    pure_message["project_principles"].extend(emotion_tags)
                    pure_message["project_principles"].extend(purpose_tags)
                
                # Add action tags as regular tags
                action_tags = [tag for tag in message.get("tags", []) if tag.startswith("#ACTION_")]
                if action_tags:
                    pure_message["tags"] = action_tags
                
                # Add truth and efficiency if available
                if "confidence_score" in metadata:
                    confidence_score = metadata["confidence_score"]
                    pure_message["truth_and_efficiency"] = {
                        "certainty_level": int(confidence_score * 100),
                        "lean_check": "Yes"
                    }
                
                pure_ai_messages.append(pure_message)
            
            return pure_ai_messages
        except Exception as e:
            logger.error(f"Error converting transcript {transcript_id} to PURE_AI format: {str(e)}")
            return []
    
    def _process_deepsearch_transcript(self,
                                      transcript_data: Union[str, List[Dict[str, Any]]],
                                      transcript_id: str,
                                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a transcript in DeepSearch format
        
        Args:
            transcript_data: Transcript data in DeepSearch format
            transcript_id: Transcript identifier
            metadata: Additional metadata
            
        Returns:
            transcript_id: Identifier of the processed transcript
        """
        logger.info(f"Processing DeepSearch transcript {transcript_id}")
        
        try:
            # Parse DeepSearch format if provided as string
            if isinstance(transcript_data, str):
                try:
                    transcript_data = json.loads(transcript_data)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid DeepSearch format: {str(e)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # Validate DeepSearch format
            if not isinstance(transcript_data, list):
                error_msg = "DeepSearch transcript must be a list of sections"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Store the transcript metadata
            transcript_metadata = {
                "memory_id": f"transcript_{transcript_id}",
                "transcript_id": transcript_id,
                "format": "deepsearch",
                "processed_at": datetime.now().isoformat(),
                "message_count": len(transcript_data),
                "status": "processed"
            }
            
            if metadata:
                transcript_metadata.update(metadata)
            
            # Store in memory system
            try:
                self.memory.store(
                    content={"deepsearch_sections": transcript_data},
                    context_id=self.transcript_context_id,
                    metadata=transcript_metadata,
                    tags=["transcript", "deepsearch"],
                    initial_tier=TIER_REFERENCE
                )
            except Exception as e:
                logger.error(f"Error storing transcript metadata: {str(e)}")
                
                # Store in mock storage if memory system fails
                if self.use_mock:
                    self._transcripts[transcript_id] = {
                        "transcript_id": transcript_id,
                        "content": {"deepsearch_sections": transcript_data},
                        "metadata": transcript_metadata,
                        "tags": ["transcript", "deepsearch"]
                    }
            
            # Process each DeepSearch section as a message
            message_count = 0
            
            for section in transcript_data:
                # Extract section data
                section_id = section.get("id", str(uuid.uuid4()))
                summary = section.get("summary", "")
                tags = section.get("tags", [])
                text = section.get("text", summary)
                
                # Parse confidence scores from summary
                confidence_scores = []
                clean_summary = summary
                
                # Extract confidence scores if present in [score1,score2,...] format
                confidence_match = re.match(r'\[([\d\.,]+)\]\s*(.*)', summary)
                if confidence_match:
                    confidence_str = confidence_match.group(1)
                    clean_summary = confidence_match.group(2)
                    
                    try:
                        confidence_scores = [float(score.strip()) for score in confidence_str.split(',')]
                    except ValueError:
                        logger.warning(f"Failed to parse confidence scores: {confidence_str}")
                
                # Convert DeepSearch tags to our tag format
                our_tags = []
                
                for ds_tag in tags:
                    tag_category = ds_tag.get("tag", "").replace("#", "")
                    tag_topic = ds_tag.get("topic", "")
                    
                    if tag_category and tag_topic:
                        our_tag = f"#{tag_category}_{tag_topic.upper()}"
                        our_tags.append(our_tag)
                
                # Generate a message ID based on section ID
                message_id = f"{transcript_id}_{section_id}"
                
                # Add the message
                self.add_message(
                    transcript_id=transcript_id,
                    content=text,
                    message_type="transcript_section",
                    sender_id="deepsearch",  # DeepSearch is considered the sender
                    receiver_id="system",
                    message_id=message_id,
                    tags=our_tags,
                    metadata={
                        "position": message_count,
                        "original_id": section_id,
                        "confidence_scores": confidence_scores,
                        "summary": clean_summary
                    }
                )
                
                message_count += 1
            
            logger.info(f"Processed DeepSearch transcript {transcript_id} with {message_count} sections")
            
            return transcript_id
        except Exception as e:
            logger.error(f"Error processing DeepSearch transcript {transcript_id}: {str(e)}")
            
            # Create error transcript in mock storage
            if self.use_mock:
                self._transcripts[transcript_id] = {
                    "transcript_id": transcript_id,
                    "error": str(e),
                    "status": "error",
                    "format": "deepsearch",
                    "created_at": datetime.now().isoformat()
                }
            
            # Re-raise to be handled by the caller
            raise
    
    def _process_pure_ai_transcript(self,
                                   transcript_data: Union[str, List[Dict[str, Any]]],
                                   transcript_id: str,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a transcript in PURE_AI_LANGUAGE format
        
        Args:
            transcript_data: Transcript data in PURE_AI_LANGUAGE format
            transcript_id: Transcript identifier
            metadata: Additional metadata
            
        Returns:
            transcript_id: Identifier of the processed transcript
        """
        logger.info(f"Processing PURE_AI transcript {transcript_id}")
        
        try:
            # Parse PURE_AI format if provided as string
            if isinstance(transcript_data, str):
                try:
                    transcript_data = json.loads(transcript_data)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid PURE_AI format: {str(e)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # Convert to list if single message
            if isinstance(transcript_data, dict):
                transcript_data = [transcript_data]
            
            # Validate PURE_AI format
            if not isinstance(transcript_data, list):
                error_msg = "PURE_AI transcript must be a list of messages"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Store the transcript metadata
            transcript_metadata = {
                "memory_id": f"transcript_{transcript_id}",
                "transcript_id": transcript_id,
                "format": "pure_ai",
                "processed_at": datetime.now().isoformat(),
                "message_count": len(transcript_data),
                "status": "processed"
            }
            
            if metadata:
                transcript_metadata.update(metadata)
            
            # Store in memory system
            try:
                self.memory.store(
                    content={"pure_ai_messages": transcript_data},
                    context_id=self.transcript_context_id,
                    metadata=transcript_metadata,
                    tags=["transcript", "pure_ai"],
                    initial_tier=TIER_REFERENCE
                )
            except Exception as e:
                logger.error(f"Error storing transcript metadata: {str(e)}")
                
                # Store in mock storage if memory system fails
                if self.use_mock:
                    self._transcripts[transcript_id] = {
                        "transcript_id": transcript_id,
                        "content": {"pure_ai_messages": transcript_data},
                        "metadata": transcript_metadata,
                        "tags": ["transcript", "pure_ai"]
                    }
            
            # Process each PURE_AI message
            message_count = 0
            
            for message in transcript_data:
                # Extract message data
                message_id = message.get("message_id", str(uuid.uuid4()))
                message_type = message.get("message_type", "information")
                sender_id = message.get("sender_id", "unknown")
                receiver_id = message.get("receiver_id", "unknown")
                content = message.get("content", {})
                
                # Extract tags from principles and tags fields
                our_tags = []
                
                # Process project principles as tags
                principles = message.get("project_principles", [])
                for principle in principles:
                    # Convert principle to tag format if needed
                    if not principle.startswith("#"):
                        principle = f"#{principle}"
                    our_tags.append(principle)
                
                # Add existing tags
                tags = message.get("tags", [])
                our_tags.extend(tags)
                
                # Extract truth and efficiency
                confidence_score = None
                truth_efficiency = message.get("truth_and_efficiency", {})
                if truth_efficiency:
                    certainty_level = truth_efficiency.get("certainty_level")
                    if certainty_level is not None:
                        confidence_score = certainty_level / 100.0
                
                # Add the message
                self.add_message(
                    transcript_id=transcript_id,
                    content=content,
                    message_type=message_type,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    message_id=message_id,
                    tags=our_tags,
                    metadata={
                        "position": message_count,
                        "protocol_version": message.get("protocol_version"),
                        "confidence_score": confidence_score
                    }
                )
                
                message_count += 1
            
            logger.info(f"Processed PURE_AI transcript {transcript_id} with {message_count} messages")
            
            return transcript_id
        except Exception as e:
            logger.error(f"Error processing PURE_AI transcript {transcript_id}: {str(e)}")
            
            # Create error transcript in mock storage
            if self.use_mock:
                self._transcripts[transcript_id] = {
                    "transcript_id": transcript_id,
                    "error": str(e),
                    "status": "error",
                    "format": "pure_ai",
                    "created_at": datetime.now().isoformat()
                }
            
            # Re-raise to be handled by the caller
            raise
    
    def _process_structured_transcript(self,
                                      transcript_data: Dict[str, Any],
                                      transcript_id: str,
                                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a transcript in structured format
        
        Args:
            transcript_data: Transcript data in structured format
            transcript_id: Transcript identifier
            metadata: Additional metadata
            
        Returns:
            transcript_id: Identifier of the processed transcript
        """
        logger.info(f"Processing structured transcript {transcript_id}")
        
        try:
            # Parse structured format if provided as string
            if isinstance(transcript_data, str):
                try:
                    transcript_data = json.loads(transcript_data)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid structured format: {str(e)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # Validate structured format
            if not isinstance(transcript_data, dict):
                error_msg = "Structured transcript must be a dictionary"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Extract messages
            messages = transcript_data.get("messages", [])
            
            if not isinstance(messages, list):
                error_msg = "Structured transcript messages must be a list"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Store the transcript metadata
            transcript_metadata = {
                "memory_id": f"transcript_{transcript_id}",
                "transcript_id": transcript_id,
                "format": "structured",
                "processed_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "status": "processed"
            }
            
            # Add provided metadata
            if metadata:
                transcript_metadata.update(metadata)
            
            # Add transcript metadata from the structured data
            transcript_meta = transcript_data.get("metadata", {})
            if transcript_meta:
                transcript_metadata.update(transcript_meta)
            
            # Store in memory system
            try:
                self.memory.store(
                    content={"structured_transcript": transcript_data},
                    context_id=self.transcript_context_id,
                    metadata=transcript_metadata,
                    tags=["transcript", "structured"],
                    initial_tier=TIER_REFERENCE
                )
            except Exception as e:
                logger.error(f"Error storing transcript metadata: {str(e)}")
                
                # Store in mock storage if memory system fails
                if self.use_mock:
                    self._transcripts[transcript_id] = {
                        "transcript_id": transcript_id,
                        "content": {"structured_transcript": transcript_data},
                        "metadata": transcript_metadata,
                        "tags": ["transcript", "structured"]
                    }
            
            # Process each message
            message_count = 0
            
            for message in messages:
                # Extract message data
                message_id = message.get("id", str(uuid.uuid4()))
                message_type = message.get("type", "message")
                sender_id = message.get("sender", "unknown")
                receiver_id = message.get("receiver", "unknown")
                content = message.get("content", "")
                timestamp = message.get("timestamp")
                tags = message.get("tags", [])
                
                # Add the message
                self.add_message(
                    transcript_id=transcript_id,
                    content=content,
                    message_type=message_type,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    message_id=message_id,
                    tags=tags,
                    metadata={
                        "position": message_count,
                        "timestamp": timestamp
                    }
                )
                
                message_count += 1
            
            logger.info(f"Processed structured transcript {transcript_id} with {message_count} messages")
            
            return transcript_id
        except Exception as e:
            logger.error(f"Error processing structured transcript {transcript_id}: {str(e)}")
            
            # Create error transcript in mock storage
            if self.use_mock:
                self._transcripts[transcript_id] = {
                    "transcript_id": transcript_id,
                    "error": str(e),
                    "status": "error",
                    "format": "structured",
                    "created_at": datetime.now().isoformat()
                }
            
            # Re-raise to be handled by the caller
            raise
    
    def _analyze_direction_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze communication direction patterns
        
        Args:
            messages: List of messages
            
        Returns:
            Analysis results
        """
        try:
            # Count messages by direction
            direction_counts = {
                DIRECTION_INTRA_AI: 0,
                DIRECTION_INTER_AI: 0,
                DIRECTION_HUMAN_AI: 0
            }
            
            for message in messages:
                tags = message.get("tags", [])
                
                # Count by direction
                if DIRECTION_INTRA_AI in tags:
                    direction_counts[DIRECTION_INTRA_AI] += 1
                elif DIRECTION_INTER_AI in tags:
                    direction_counts[DIRECTION_INTER_AI] += 1
                elif DIRECTION_HUMAN_AI in tags:
                    direction_counts[DIRECTION_HUMAN_AI] += 1
            
            # Calculate percentages
            total_messages = len(messages)
            direction_percentages = {}
            
            for direction, count in direction_counts.items():
                if total_messages > 0:
                    percentage = (count / total_messages) * 100
                else:
                    percentage = 0
                
                direction_percentages[direction] = percentage
            
            return {
                "counts": direction_counts,
                "percentages": direction_percentages
            }
        except Exception as e:
            logger.error(f"Error analyzing direction patterns: {str(e)}")
            return {
                "counts": {},
                "percentages": {}
            }
    
    def _analyze_purpose_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze communication purpose patterns
        
        Args:
            messages: List of messages
            
        Returns:
            Analysis results
        """
        try:
            # Count messages by purpose
            purpose_counts = {
                PURPOSE_CLARIFICATION: 0,
                PURPOSE_IDEATION: 0,
                PURPOSE_DECISION: 0,
                PURPOSE_IMPLEMENTATION: 0,
                PURPOSE_FEEDBACK: 0
            }
            
            for message in messages:
                tags = message.get("tags", [])
                
                # Count by purpose
                for purpose in purpose_counts.keys():
                    if purpose in tags:
                        purpose_counts[purpose] += 1
            
            # Calculate percentages
            total_messages = len(messages)
            purpose_percentages = {}
            
            for purpose, count in purpose_counts.items():
                if total_messages > 0:
                    percentage = (count / total_messages) * 100
                else:
                    percentage = 0
                
                purpose_percentages[purpose] = percentage
            
            return {
                "counts": purpose_counts,
                "percentages": purpose_percentages
            }
        except Exception as e:
            logger.error(f"Error analyzing purpose patterns: {str(e)}")
            return {
                "counts": {},
                "percentages": {}
            }
    
    def _analyze_emotion_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze emotional patterns
        
        Args:
            messages: List of messages
            
        Returns:
            Analysis results
        """
        try:
            # Count messages by emotion
            emotion_counts = {
                EMOTION_EXCITEMENT: 0,
                EMOTION_FRUSTRATION: 0,
                EMOTION_SATISFACTION: 0,
                EMOTION_CONFUSION: 0
            }
            
            for message in messages:
                tags = message.get("tags", [])
                
                # Count by emotion
                for emotion in emotion_counts.keys():
                    if emotion in tags:
                        emotion_counts[emotion] += 1
            
            # Calculate percentages
            total_messages = len(messages)
            emotion_percentages = {}
            
            for emotion, count in emotion_counts.items():
                if total_messages > 0:
                    percentage = (count / total_messages) * 100
                else:
                    percentage = 0
                
                emotion_percentages[emotion] = percentage
            
            return {
                "counts": emotion_counts,
                "percentages": emotion_percentages
            }
        except Exception as e:
            logger.error(f"Error analyzing emotion patterns: {str(e)}")
            return {
                "counts": {},
                "percentages": {}
            }
    
    def _analyze_action_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze action patterns
        
        Args:
            messages: List of messages
            
        Returns:
            Analysis results
        """
        try:
            # Count messages by action
            action_counts = {
                ACTION_REQUESTED: 0,
                ACTION_ASSIGNED: 0,
                ACTION_COMPLETED: 0,
                ACTION_BLOCKED: 0
            }
            
            for message in messages:
                tags = message.get("tags", [])
                
                # Count by action
                for action in action_counts.keys():
                    if action in tags:
                        action_counts[action] += 1
            
            # Calculate percentages
            total_messages = len(messages)
            action_percentages = {}
            
            for action, count in action_counts.items():
                if total_messages > 0:
                    percentage = (count / total_messages) * 100
                else:
                    percentage = 0
                
                action_percentages[action] = percentage
            
            # Calculate completion rate
            requested = action_counts[ACTION_REQUESTED] + action_counts[ACTION_ASSIGNED]
            completed = action_counts[ACTION_COMPLETED]
            
            if requested > 0:
                completion_rate = (completed / requested) * 100
            else:
                completion_rate = 0
            
            return {
                "counts": action_counts,
                "percentages": action_percentages,
                "completion_rate": completion_rate
            }
        except Exception as e:
            logger.error(f"Error analyzing action patterns: {str(e)}")
            return {
                "counts": {},
                "percentages": {},
                "completion_rate": 0
            }
    
    def _calculate_communication_metrics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate communication metrics
        
        Args:
            messages: List of messages
            
        Returns:
            Metrics
        """
        try:
            # Calculate basic metrics
            total_messages = len(messages)
            
            if total_messages == 0:
                return {}
            
            # Group by sender
            senders = {}
            
            for message in messages:
                sender = message.get("metadata", {}).get("sender_id", "unknown")
                
                if sender not in senders:
                    senders[sender] = []
                
                senders[sender].append(message)
            
            # Calculate tokens per message (estimated)
            total_tokens = 0
            
            for message in messages:
                content = message.get("content", "")
                
                if isinstance(content, str):
                    # Rough estimation - 4 chars per token
                    tokens = len(content) / 4
                elif isinstance(content, dict):
                    # Rough estimation for structured content
                    content_str = json.dumps(content)
                    tokens = len(content_str) / 4
                else:
                    tokens = 0
                
                total_tokens += tokens
            
            avg_tokens_per_message = total_tokens / total_messages if total_messages > 0 else 0
            
            # Calculate response times (if timestamp available)
            response_times = []
            
            # Sort messages by timestamp
            try:
                sorted_messages = sorted(
                    messages, 
                    key=lambda m: datetime.fromisoformat(m.get("metadata", {}).get("timestamp", "")) 
                    if isinstance(m.get("metadata", {}).get("timestamp", ""), str) else 0
                )
                
                for i in range(1, len(sorted_messages)):
                    curr_msg = sorted_messages[i]
                    prev_msg = sorted_messages[i-1]
                    
                    curr_time_str = curr_msg.get("metadata", {}).get("timestamp")
                    prev_time_str = prev_msg.get("metadata", {}).get("timestamp")
                    
                    if curr_time_str and prev_time_str:
                        try:
                            # Convert to datetime if they're strings
                            curr_time = curr_time_str if isinstance(curr_time_str, datetime) else datetime.fromisoformat(curr_time_str)
                            prev_time = prev_time_str if isinstance(prev_time_str, datetime) else datetime.fromisoformat(prev_time_str)
                            
                            # Calculate time difference in seconds
                            time_diff = (curr_time - prev_time).total_seconds()
                            if time_diff > 0:  # Only add positive time differences
                                response_times.append(time_diff)
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Error parsing timestamps: {e}")
            except Exception as e:
                logger.warning(f"Error calculating response times: {e}")
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Prepare metrics
            metrics = {
                "message_count": total_messages,
                "unique_senders": len(senders),
                "avg_tokens_per_message": avg_tokens_per_message,
                "avg_response_time_seconds": avg_response_time,
                "sender_distribution": {sender: len(msgs) for sender, msgs in senders.items()}
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating communication metrics: {str(e)}")
            return {
                "message_count": len(messages),
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the transcript processor
        
        Returns:
            Status information
        """
        status = {
            "status": "active",
            "mode": "mock" if self.use_mock else "normal",
            "memory_system_available": self.memory is not None,
            "confidence_threshold": self.confidence_threshold
        }
        
        # Add message counts if in mock mode
        if self.use_mock:
            status["transcript_count"] = len(getattr(self, '_transcripts', {}))
            status["message_count"] = len(getattr(self, '_messages', {}))
        
        return status


# Convenience function to create transcript processor
def create_transcript_processor(
    memory_system=None, 
    project_id=None, 
    collection_prefix="",
    use_mock=False
) -> TranscriptProcessor:
    """
    Create a transcript processor instance with robust error handling
    
    Args:
        memory_system: Optional memory system
        project_id: Google Cloud project ID
        collection_prefix: Collection prefix
        use_mock: Whether to use mock mode
        
    Returns:
        TranscriptProcessor instance
    """
    # Check environment for mock mode setting
    env_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
    use_mock = use_mock or env_mock
    
    try:
        processor = TranscriptProcessor(
            memory_system=memory_system,
            project_id=project_id,
            collection_prefix=collection_prefix,
            use_mock=use_mock
        )
        logger.info("Created transcript processor instance")
        return processor
    except Exception as e:
        logger.error(f"Error creating transcript processor: {str(e)}")
        # Create with mock mode as fallback
        try:
            processor = TranscriptProcessor(
                memory_system=None,
                project_id=None,
                collection_prefix="",
                use_mock=True
            )
            logger.warning("Created transcript processor instance in fallback mock mode")
            return processor
        except Exception as e2:
            logger.critical(f"Critical error creating transcript processor even in mock mode: {str(e2)}")
            raise