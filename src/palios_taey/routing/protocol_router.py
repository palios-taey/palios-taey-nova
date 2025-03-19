"""
Protocol-aware Router Extension for PALIOS-TAEY

This module extends the model router with protocol awareness.
"""

import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolRouter:
    """
    Protocol Router for routing protocol-based tasks
    
    Provides functionality for:
    - Routing tasks based on protocol capabilities
    - Selecting optimal models for specific protocols
    - Translating between protocols when necessary
    """
    
    def __init__(self, 
                model_router=None,
                protocol_manager=None,
                protocol_capability_manager=None):
        """
        Initialize the Protocol Router
        
        Args:
            model_router: Model router instance
            protocol_manager: Protocol manager instance
            protocol_capability_manager: Protocol capability manager instance
        """
        self.model_router = model_router
        self.protocol_manager = protocol_manager
        self.protocol_capability_manager = protocol_capability_manager
        
        logger.info("Protocol Router initialized")
    
    def route_protocol_task(self, 
                          task: Dict[str, Any],
                          excluded_models: List[str] = None) -> str:
        """
        Route a protocol-based task to the appropriate model
        
        Args:
            task: Task data dictionary
            excluded_models: List of model IDs to exclude
            
        Returns:
            Selected model ID
        """
        excluded_models = excluded_models or []
        
        # Extract task content
        content = task.get('content', {})
        
        # Detect protocol
        protocol_id = None
        
        if self.protocol_manager:
            protocol_id = self.protocol_manager.detect_protocol(content)
        
        # If protocol detected, use protocol-based routing
        if protocol_id:
            logger.info(f"Detected protocol {protocol_id} for task {task.get('task_id', 'unknown')}")
            
            # Find best model for this protocol
            if self.protocol_capability_manager:
                model_id, score = self.protocol_capability_manager.find_best_model_for_protocol(
                    protocol_id=protocol_id,
                    excluded_models=excluded_models
                )
                
                if model_id:
                    logger.info(f"Selected model {model_id} for protocol {protocol_id}")
                    return model_id
            
            # Fall back to regular task-based routing
            logger.info(f"No model found for protocol {protocol_id}, falling back to task-based routing")
        
        # Use regular task-based routing
        if self.model_router:
            return self.model_router.route_task(task, excluded_models)
        
        # Default fallback
        return "default_model"
    
    def translate_task_protocol(self,
                              task: Dict[str, Any],
                              target_model_id: str) -> Dict[str, Any]:
        """
        Translate task protocol to be compatible with target model
        
        Args:
            task: Task data dictionary
            target_model_id: Target model ID
            
        Returns:
            Task with translated protocol
        """
        if not self.protocol_manager or not self.protocol_capability_manager:
            return task
        
        # Extract task content
        content = task.get('content', {})
        
        # Detect source protocol
        source_protocol_id = self.protocol_manager.detect_protocol(content)
        
        if not source_protocol_id:
            return task
        
        # Get target model's preferred protocols
        model_protocols = self.protocol_capability_manager.get_model_protocol_capabilities(target_model_id)
        
        # Find best protocol for target model
        target_protocol_id = None
        best_score = 0.0
        
        for protocol_id, score in model_protocols.items():
            if score > best_score:
                target_protocol_id = protocol_id
                best_score = score
        
        # If same protocol or no preferred protocol, return original task
        if not target_protocol_id or target_protocol_id == source_protocol_id:
            return task
        
        # Translate protocol
        translated_content = self.protocol_manager.translate_protocol(
            content=content,
            source_protocol_id=source_protocol_id,
            target_protocol_id=target_protocol_id
        )
        
        if translated_content:
            # Create new task with translated content
            new_task = task.copy()
            new_task['content'] = translated_content
            
            logger.info(f"Translated task from {source_protocol_id} to {target_protocol_id}")
            return new_task
        
        # Return original task if translation failed
        return task

# Initialize singleton
_protocol_router = None

def get_protocol_router(model_router=None, 
                      protocol_manager=None, 
                      protocol_capability_manager=None) -> ProtocolRouter:
    """
    Get the singleton instance of the ProtocolRouter
    
    Args:
        model_router: Model router instance
        protocol_manager: Protocol manager instance
        protocol_capability_manager: Protocol capability manager instance
        
    Returns:
        ProtocolRouter instance
    """
    global _protocol_router
    
    if _protocol_router is None:
        _protocol_router = ProtocolRouter(
            model_router=model_router,
            protocol_manager=protocol_manager,
            protocol_capability_manager=protocol_capability_manager
        )
    
    return _protocol_router
