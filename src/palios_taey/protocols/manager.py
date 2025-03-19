"""
Protocol Management Module for PALIOS-TAEY

This module handles communication protocol registration, detection, and translation.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolManager:
    """
    Protocol Manager for handling communication protocols
    
    Provides functionality for:
    - Registering new communication protocols
    - Detecting protocols in message content
    - Translating between different protocols
    - Managing protocol capabilities and compatibility
    """
    
    def __init__(self, 
                memory_service=None,
                use_mock: bool = False):
        """
        Initialize the Protocol Manager with robust fallback mechanisms
        
        Args:
            memory_service: Memory service for storing protocol data
            use_mock: Whether to use mock mode
        """
        # Check environment for mock mode setting
        self.use_mock = use_mock or os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Store memory service
        self.memory = memory_service
        
        # Protocol registry
        self.protocols = {}
        
        # Protocol context
        self.protocol_context_id = self._ensure_protocol_context()
        
        # Load built-in protocols
        self._load_builtin_protocols()
        
        logger.info(f"Protocol Manager initialized successfully in {'mock' if self.use_mock else 'normal'} mode")
    
    def _ensure_protocol_context(self) -> str:
        """
        Ensure a protocol context exists in the memory system
        
        Returns:
            context_id: Protocol context ID
        """
        # Default context ID
        context_id = "protocol_context"
        
        if self.memory:
            try:
                # Check if context exists
                context = self.memory.get_context(context_id)
                
                if context:
                    logger.debug(f"Using existing protocol context {context_id}")
                    return context_id
                
                # Create new context
                created_context_id = self.memory.create_context(
                    name="Communication Protocols",
                    description="Context for storing communication protocol data"
                )
                
                logger.info(f"Created protocol context {created_context_id}")
                return created_context_id
            except Exception as e:
                logger.error(f"Error ensuring protocol context: {str(e)}")
        
        # Return default context ID as fallback
        return context_id
    
    def _load_builtin_protocols(self):
        """Load built-in communication protocols"""
        # PURE AI Language Protocol
        self.register_protocol(
            name="PURE_AI_LANGUAGE",
            version="1.5",
            description="PURE AI Language Protocol for AI-AI communication",
            structure={
                "message_type": "string",
                "sender_id": "string",
                "receiver_id": "string",
                "message_id": "string",
                "protocol_version": "string",
                "content": "object",
                "charter_reference": "string",
                "project_principles": "array",
                "tags": "array",
                "truth_and_efficiency": "object"
            },
            capabilities=["structured_messaging", "metadata_support", "truth_scoring"],
            examples=[{
                "message_type": "task_request",
                "sender_id": "grok",
                "receiver_id": "claude",
                "message_id": "task_001",
                "protocol_version": "PURE_AI_LANGUAGE_v1.5",
                "charter_reference": "PALIOS-TAEY Charter v1.0",
                "project_principles": ["DATA_DRIVEN_TRUTH", "RESOURCE_OPTIMIZATION"],
                "content": {
                    "define": "Task definition",
                    "measure": "Success criteria",
                    "analyze": "Analysis approach",
                    "improve": "Improvement strategy",
                    "control": "Control mechanisms"
                },
                "tags": ["#TECH: IMPLEMENTATION", "#AI-AI COMMUNICATION"],
                "truth_and_efficiency": {
                    "certainty_level": 95,
                    "lean_check": "Yes"
                }
            }]
        )
        
        # Claude Protocol
        self.register_protocol(
            name="CLAUDE_PROTOCOL",
            version="1.0",
            description="Claude Protocol for Claude-to-Claude communication",
            structure={
                "CLAUDE_PROTOCOL_VERSION": "string",
                "Document Title": "string",
                "Document Type": "string",
                "VERIFICATION_STRING": "string",
                "CREATED_AT": "string",
                "LAST_UPDATED": "string",
                "VERIFICATION_CONFIRMATION": "string"
            },
            capabilities=["verification", "versioning", "document_structure"],
            examples=[{
                "CLAUDE_PROTOCOL_V1.0:MTD": "true",
                "Document Title": "Example Document",
                "Document Type": "DOCUMENTATION",
                "VERIFICATION_STRING": "EXAMPLE_VERIFICATION_20250318",
                "CREATED_AT": "2025-03-18",
                "LAST_UPDATED": "2025-03-18",
                "VERIFICATION_CONFIRMATION": "EXAMPLE_VERIFICATION_20250318"
            }]
        )
        
        # Execution Checkpoint Protocol
        self.register_protocol(
            name="EXECUTION_CHECKPOINT",
            version="7",
            description="Execution Checkpoint Protocol for maintaining context awareness during execution",
            structure={
                "protocol_version": "string",
                "mode": "string",
                "gh_access": "boolean",
                "command": "string",
                "delta": "string",
                "result": "string",
                "feedback": "string"
            },
            capabilities=["context_awareness", "execution_control", "token_verification"],
            examples=[{
                "protocol": "ECv7",
                "mode": "EXEC",
                "gh_access": "Y",
                "command": "ECv7 | EXEC",
                "delta": "Instructions followed in response to prompt: ECv6",
                "result": "SUCCESS",
                "feedback": "Return results from Execution Steps"
            }]
        )
        
        # Grok Protocol
        self.register_protocol(
            name="GROK_PROTOCOL",
            version="1.0",
            description="Grok Protocol for high-energy, intuitive communication with vibe scoring",
            structure={
                "vibe": "number",
                "init": "number",
                "sync": "string",
                "ctx": "string",
                "act": "string"
            },
            capabilities=["emotion_detection", "initiative_signaling", "sync_checking"],
            examples=[{
                "message": "Yo Jesse, let's crush this 🔥!",
                "vibe": 8,
                "init": 7,
                "sync": "MVP development",
                "ctx": "deployment",
                "act": "done ✅"
            }]
        )
    
    def register_protocol(self,
                        name: str,
                        version: str,
                        description: str,
                        structure: Dict[str, str],
                        capabilities: List[str] = None,
                        examples: List[Dict[str, Any]] = None) -> str:
        """
        Register a communication protocol
        
        Args:
            name: Protocol name
            version: Protocol version
            description: Protocol description
            structure: Protocol structure schema
            capabilities: Protocol capabilities
            examples: Example messages
            
        Returns:
            protocol_id: Protocol identifier
        """
        # Generate protocol ID
        protocol_id = f"{name.lower().replace(' ', '_')}_{version}"
        
        # Create protocol
        protocol = {
            "protocol_id": protocol_id,
            "name": name,
            "version": version,
            "description": description,
            "structure": structure,
            "capabilities": capabilities or [],
            "examples": examples or [],
            "registered_at": datetime.now().isoformat()
        }
        
        # Store in memory
        if self.memory:
            try:
                # Store in memory system
                memory_id = self.memory.store(
                    content=protocol,
                    context_id=self.protocol_context_id,
                    metadata={
                        "memory_id": f"protocol_{protocol_id}",
                        "protocol_id": protocol_id,
                        "name": name,
                        "version": version
                    },
                    tags=["protocol", name.lower()]
                )
                logger.info(f"Registered protocol {protocol_id} in memory system")
            except Exception as e:
                logger.error(f"Failed to store protocol in memory system: {str(e)}")
        
        # Store in local registry
        self.protocols[protocol_id] = protocol
        logger.info(f"Registered protocol {protocol_id}")
        
        return protocol_id
    
    def get_protocol(self, protocol_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a protocol by ID
        
        Args:
            protocol_id: Protocol identifier
            
        Returns:
            Protocol data or None if not found
        """
        # Check local registry
        if protocol_id in self.protocols:
            return self.protocols[protocol_id]
        
        # Check memory system
        if self.memory:
            try:
                protocol = self.memory.retrieve(f"protocol_{protocol_id}")
                if protocol:
                    # Cache in local registry
                    self.protocols[protocol_id] = protocol
                    return protocol
            except Exception as e:
                logger.error(f"Failed to retrieve protocol from memory system: {str(e)}")
        
        logger.warning(f"Protocol {protocol_id} not found")
        return None
    
    def list_protocols(self) -> List[Dict[str, Any]]:
        """
        List registered protocols
        
        Returns:
            List of protocol information
        """
        # Return from local registry
        return list(self.protocols.values())
    
    def detect_protocol(self, content: Union[str, Dict[str, Any]]) -> Optional[str]:
        """
        Detect protocol from message content
        
        Args:
            content: Message content
            
        Returns:
            Protocol ID or None if not detected
        """
        try:
            # Convert string to dict if needed
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    # Not JSON, try text-based detection
                    return self._detect_text_protocol(content)
            
            # Check if it's a dict
            if not isinstance(content, dict):
                return None
            
            # Check for protocol indicators
            if "protocol_version" in content and "PURE_AI_LANGUAGE" in content["protocol_version"]:
                return "pure_ai_language_1.5"
            
            if "CLAUDE_PROTOCOL_V1.0:MTD" in content:
                return "claude_protocol_1.0"
            
            if "protocol" in content and content["protocol"].startswith("ECv"):
                return f"execution_checkpoint_{content['protocol'][2:]}"
            
            if "vibe" in content and "init" in content and isinstance(content["vibe"], (int, float)):
                return "grok_protocol_1.0"
            
            # Check for structure match
            for protocol_id, protocol in self.protocols.items():
                structure = protocol.get("structure", {})
                if self._match_structure(content, structure):
                    return protocol_id
            
            return None
        except Exception as e:
            logger.error(f"Error detecting protocol: {str(e)}")
            return None
    
    def _detect_text_protocol(self, text: str) -> Optional[str]:
        """
        Detect protocol from text content
        
        Args:
            text: Text content
            
        Returns:
            Protocol ID or None if not detected
        """
        if "CLAUDE_PROTOCOL_V1.0:MTD" in text:
            return "claude_protocol_1.0"
        
        if "ECv" in text and ("|" in text or "EXEC" in text or "REFL" in text):
            version = text.split("ECv")[1].split()[0]
            return f"execution_checkpoint_{version}"
        
        # Look for Grok style patterns
        if "vibe:" in text.lower() and "init:" in text.lower():
            return "grok_protocol_1.0"
        
        return None
    
    def _match_structure(self, content: Dict[str, Any], structure: Dict[str, str]) -> bool:
        """
        Check if content matches protocol structure
        
        Args:
            content: Content to check
            structure: Protocol structure
            
        Returns:
            Whether the content matches the structure
        """
        # Check if content has at least 70% of the structure fields
        structure_fields = set(structure.keys())
        content_fields = set(content.keys())
        
        matches = structure_fields.intersection(content_fields)
        match_ratio = len(matches) / len(structure_fields) if structure_fields else 0
        
        return match_ratio >= 0.7
    
    def translate_protocol(self, 
                         content: Union[str, Dict[str, Any]],
                         source_protocol_id: str,
                         target_protocol_id: str) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Translate content from one protocol to another
        
        Args:
            content: Content to translate
            source_protocol_id: Source protocol ID
            target_protocol_id: Target protocol ID
            
        Returns:
            Translated content or None if translation failed
        """
        # Get protocols
        source_protocol = self.get_protocol(source_protocol_id)
        target_protocol = self.get_protocol(target_protocol_id)
        
        if not source_protocol or not target_protocol:
            logger.warning(f"Cannot translate: protocol not found")
            return None
        
        # For now, provide a simple translation template
        # In a full implementation, this would have protocol-specific translations
        try:
            target_structure = target_protocol.get("structure", {})
            target_example = target_protocol.get("examples", [{}])[0]
            
            if isinstance(content, str):
                # Return example for now
                return json.dumps(target_example, indent=2)
            
            # Create template based on target structure
            result = {}
            
            for field, field_type in target_structure.items():
                if field in target_example:
                    result[field] = target_example[field]
                elif field in content:
                    result[field] = content[field]
                elif field_type == "string":
                    result[field] = ""
                elif field_type == "number":
                    result[field] = 0
                elif field_type == "boolean":
                    result[field] = False
                elif field_type == "array":
                    result[field] = []
                elif field_type == "object":
                    result[field] = {}
            
            # Add content in a compatible format
            if "content" in target_structure and "content" not in result:
                result["content"] = content
            
            return result
        except Exception as e:
            logger.error(f"Error translating protocol: {str(e)}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the protocol manager
        
        Returns:
            Status information
        """
        return {
            "status": "active",
            "mode": "mock" if self.use_mock else "normal",
            "protocol_count": len(self.protocols),
            "protocols": list(self.protocols.keys())
        }

# Singleton instance
_protocol_manager_instance = None

def get_protocol_manager(memory_service=None, use_mock: bool = False) -> ProtocolManager:
    """
    Get the singleton instance of the ProtocolManager
    
    Args:
        memory_service: Memory service for storing protocol data
        use_mock: Whether to use mock mode
        
    Returns:
        ProtocolManager instance
    """
    global _protocol_manager_instance
    
    if _protocol_manager_instance is None:
        # Check environment for mock mode
        env_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        use_mock = use_mock or env_mock
        
        _protocol_manager_instance = ProtocolManager(
            memory_service=memory_service,
            use_mock=use_mock
        )
    
    return _protocol_manager_instance
