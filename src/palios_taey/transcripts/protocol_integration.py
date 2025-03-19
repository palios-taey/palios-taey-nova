"""
Protocol Integration for Transcript Processor

This module integrates the protocol manager with the transcript processor.
"""

import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptProtocolIntegration:
    """
    Transcript Protocol Integration for adding protocol awareness to the transcript processor
    
    Provides functionality for:
    - Detecting protocols in transcripts
    - Adding protocol-specific tags
    - Processing protocol-specific message formats
    """
    
    def __init__(self, transcript_processor=None, protocol_manager=None):
        """
        Initialize the Transcript Protocol Integration
        
        Args:
            transcript_processor: Transcript processor instance
            protocol_manager: Protocol manager instance
        """
        self.transcript_processor = transcript_processor
        self.protocol_manager = protocol_manager
        
        # Protocol tag prefix
        self.protocol_tag_prefix = "#PROTOCOL_"
        
        logger.info("Transcript Protocol Integration initialized")
    
    def add_protocol_detection(self, message_content: Any, tags: List[str]) -> None:
        """
        Detect protocol in message content and add appropriate tags
        
        Args:
            message_content: Message content
            tags: List of tags to update
        """
        if not self.protocol_manager:
            return
        
        try:
            # Detect protocol
            protocol_id = self.protocol_manager.detect_protocol(message_content)
            
            if protocol_id:
                # Add protocol tag if not already present
                protocol_tag = f"{self.protocol_tag_prefix}{protocol_id.upper()}"
                
                if protocol_tag not in tags:
                    tags.append(protocol_tag)
                    
                # Get protocol details
                protocol = self.protocol_manager.get_protocol(protocol_id)
                
                if protocol:
                    # Add capability tags
                    capabilities = protocol.get("capabilities", [])
                    
                    for capability in capabilities:
                        capability_tag = f"#CAPABILITY_{capability.upper()}"
                        
                        if capability_tag not in tags:
                            tags.append(capability_tag)
        except Exception as e:
            logger.error(f"Error detecting protocol: {str(e)}")
    
    def process_transcript_with_protocol_awareness(self, 
                                                transcript_data: Union[str, Dict[str, Any], List[Dict[str, Any]]],
                                                format_type: str = "raw",
                                                transcript_id: Optional[str] = None,
                                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a transcript with protocol awareness
        
        Args:
            transcript_data: Transcript data
            format_type: Format type
            transcript_id: Optional transcript ID
            metadata: Additional metadata
            
        Returns:
            transcript_id: Identifier of the processed transcript
        """
        if not self.transcript_processor:
            logger.error("Transcript processor not available")
            return transcript_id or "error_no_processor"
        
        # Detect protocol if not specified in metadata
        if metadata is None:
            metadata = {}
        
        if "protocol_id" not in metadata and self.protocol_manager:
            try:
                protocol_id = self.protocol_manager.detect_protocol(transcript_data)
                
                if protocol_id:
                    metadata["protocol_id"] = protocol_id
                    
                    # Get protocol details
                    protocol = self.protocol_manager.get_protocol(protocol_id)
                    
                    if protocol:
                        metadata["protocol_name"] = protocol.get("name")
                        metadata["protocol_version"] = protocol.get("version")
                        
                        # Adjust format type based on protocol
                        if protocol_id.startswith("claude_protocol"):
                            format_type = "claude"
                        elif protocol_id.startswith("pure_ai_language"):
                            format_type = "pure_ai"
                        elif protocol_id.startswith("execution_checkpoint"):
                            format_type = "structured"
            except Exception as e:
                logger.error(f"Error detecting protocol: {str(e)}")
        
        # Process transcript
        processed_transcript_id = self.transcript_processor.process_transcript(
            transcript_data=transcript_data,
            format_type=format_type,
            transcript_id=transcript_id,
            metadata=metadata
        )
        
        return processed_transcript_id
    
    def enhance_transcript_processor(self):
        """Enhance the transcript processor with protocol awareness"""
        if not self.transcript_processor:
            logger.error("Transcript processor not available")
            return
        
        # Store original methods
        original_auto_detect_tags = getattr(self.transcript_processor, "_auto_detect_tags", None)
        original_process_transcript = getattr(self.transcript_processor, "process_transcript", None)
        
        if original_auto_detect_tags:
            # Override auto_detect_tags method
            def enhanced_auto_detect_tags(content, tags):
                # Call original method
                original_auto_detect_tags(content, tags)
                
                # Add protocol detection
                self.add_protocol_detection(content, tags)
            
            # Replace the method
            self.transcript_processor._auto_detect_tags = enhanced_auto_detect_tags
            logger.info("Enhanced transcript processor auto_detect_tags method")
        
        if original_process_transcript:
            # Override process_transcript method
            def enhanced_process_transcript(transcript_data, format_type="raw", transcript_id=None, metadata=None):
                return self.process_transcript_with_protocol_awareness(
                    transcript_data=transcript_data,
                    format_type=format_type,
                    transcript_id=transcript_id,
                    metadata=metadata
                )
            
            # Replace the method
            self.transcript_processor.process_transcript = enhanced_process_transcript
            logger.info("Enhanced transcript processor process_transcript method")

# Initialize singleton
_transcript_protocol_integration = None

def get_transcript_protocol_integration(transcript_processor=None, protocol_manager=None) -> TranscriptProtocolIntegration:
    """
    Get the singleton instance of the TranscriptProtocolIntegration
    
    Args:
        transcript_processor: Transcript processor instance
        protocol_manager: Protocol manager instance
        
    Returns:
        TranscriptProtocolIntegration instance
    """
    global _transcript_protocol_integration
    
    if _transcript_protocol_integration is None:
        _transcript_protocol_integration = TranscriptProtocolIntegration(
            transcript_processor=transcript_processor,
            protocol_manager=protocol_manager
        )
    
    return _transcript_protocol_integration
