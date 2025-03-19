"""
Protocol Capability Extensions for the Dynamic Model Registry

This module extends the model registry with protocol capability support.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolCapabilityManager:
    """
    Protocol Capability Manager for tracking model protocol capabilities
    
    Provides functionality for:
    - Registering protocol capabilities for models
    - Measuring protocol performance
    - Finding best models for protocol-based tasks
    """
    
    def __init__(self, model_registry=None, protocol_manager=None):
        """
        Initialize the Protocol Capability Manager
        
        Args:
            model_registry: Model registry instance
            protocol_manager: Protocol manager instance
        """
        self.model_registry = model_registry
        self.protocol_manager = protocol_manager
        
        # Protocol capabilities by model
        self.protocol_capabilities = {}
        
        # Initialize default capabilities
        self._initialize_default_capabilities()
        
        logger.info("Protocol Capability Manager initialized")
    
    def _initialize_default_capabilities(self):
        """Initialize default protocol capabilities for known models"""
        # Default capabilities for Claude
        self._register_model_protocol_capabilities(
            model_id="claude",
            capabilities={
                "claude_protocol_1.0": 0.95,
                "pure_ai_language_1.5": 0.85,
                "execution_checkpoint_7": 0.90
            }
        )
        
        # Default capabilities for Gemini
        self._register_model_protocol_capabilities(
            model_id="gemini",
            capabilities={
                "pure_ai_language_1.5": 0.90,
                "execution_checkpoint_7": 0.80,
                "grok_protocol_1.0": 0.75
            }
        )
        
        # Default capabilities for Grok
        self._register_model_protocol_capabilities(
            model_id="grok",
            capabilities={
                "pure_ai_language_1.5": 0.90,
                "grok_protocol_1.0": 0.95,
                "execution_checkpoint_7": 0.75
            }
        )
    
    def _register_model_protocol_capabilities(self, 
                                           model_id: str,
                                           capabilities: Dict[str, float]):
        """
        Register protocol capabilities for a model
        
        Args:
            model_id: Model identifier
            capabilities: Dictionary mapping protocol IDs to capability scores (0.0-1.0)
        """
        if model_id not in self.protocol_capabilities:
            self.protocol_capabilities[model_id] = {}
        
        for protocol_id, score in capabilities.items():
            self.protocol_capabilities[model_id][protocol_id] = score
    
    def register_model_protocol_capability(self,
                                         model_id: str,
                                         protocol_id: str,
                                         capability_score: float) -> bool:
        """
        Register a protocol capability for a model
        
        Args:
            model_id: Model identifier
            protocol_id: Protocol identifier
            capability_score: Capability score (0.0-1.0)
            
        Returns:
            Whether registration was successful
        """
        try:
            # Initialize model capabilities if needed
            if model_id not in self.protocol_capabilities:
                self.protocol_capabilities[model_id] = {}
            
            # Normalize score
            capability_score = min(1.0, max(0.0, capability_score))
            
            # Store capability
            self.protocol_capabilities[model_id][protocol_id] = capability_score
            
            logger.info(f"Registered protocol capability {protocol_id} for model {model_id}: {capability_score}")
            
            # Update model registry if available
            if self.model_registry:
                try:
                    # Update model registry with protocol capability
                    self.model_registry.update_capability(
                        model_id=model_id,
                        task_type=f"protocol_{protocol_id}",
                        new_score=capability_score
                    )
                except Exception as e:
                    logger.error(f"Failed to update model registry: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to register protocol capability: {str(e)}")
            return False
    
    def get_model_protocol_capabilities(self, model_id: str) -> Dict[str, float]:
        """
        Get protocol capabilities for a model
        
        Args:
            model_id: Model identifier
            
        Returns:
            Dictionary of protocol capabilities
        """
        return self.protocol_capabilities.get(model_id, {})
    
    def find_best_model_for_protocol(self, 
                                   protocol_id: str,
                                   min_capability: float = 0.7,
                                   excluded_models: List[str] = None) -> Tuple[Optional[str], float]:
        """
        Find the best model for a protocol
        
        Args:
            protocol_id: Protocol identifier
            min_capability: Minimum capability score required
            excluded_models: List of model IDs to exclude
            
        Returns:
            Tuple of (best_model_id, capability_score) or (None, 0.0) if no suitable model
        """
        excluded_models = excluded_models or []
        
        best_model = None
        best_score = 0.0
        
        for model_id, capabilities in self.protocol_capabilities.items():
            # Skip excluded models
            if model_id in excluded_models:
                continue
            
            # Get capability score for this protocol
            score = capabilities.get(protocol_id, 0.0)
            
            # Check if it meets minimum capability
            if score < min_capability:
                continue
            
            # Check if it's better than current best
            if score > best_score:
                best_model = model_id
                best_score = score
        
        # If no model found and model registry available, try to find a model with registry
        if best_model is None and self.model_registry:
            try:
                model_id, score = self.model_registry.find_best_model_for_task(
                    task_type=f"protocol_{protocol_id}",
                    min_capability=min_capability,
                    excluded_models=excluded_models
                )
                
                if model_id:
                    best_model = model_id
                    best_score = score
            except Exception as e:
                logger.error(f"Failed to find model with registry: {str(e)}")
        
        return (best_model, best_score)
    
    def record_protocol_performance(self,
                                  model_id: str,
                                  protocol_id: str,
                                  performance_metrics: Dict[str, Any],
                                  learn: bool = True) -> bool:
        """
        Record protocol performance for a model
        
        Args:
            model_id: Model identifier
            protocol_id: Protocol identifier
            performance_metrics: Dictionary of performance metrics
            learn: Whether to update capabilities based on performance
            
        Returns:
            Whether recording was successful
        """
        try:
            # Calculate performance score
            success = performance_metrics.get('success', False)
            quality = performance_metrics.get('quality', 0.5)
            efficiency = performance_metrics.get('efficiency', 0.5)
            
            # Calculate base score from success/failure
            base_score = 0.7 if success else 0.3
            
            # Adjust based on quality and efficiency
            performance_score = base_score * 0.4 + quality * 0.4 + efficiency * 0.2
            
            # Update model registry if available
            if self.model_registry:
                try:
                    # Record performance with registry
                    self.model_registry.record_performance(
                        model_id=model_id,
                        task_type=f"protocol_{protocol_id}",
                        performance_metrics=performance_metrics,
                        learn=learn
                    )
                except Exception as e:
                    logger.error(f"Failed to record performance with registry: {str(e)}")
            
            # Update capabilities if learning is enabled
            if learn:
                # Get current capability
                current_capability = self.get_model_protocol_capabilities(model_id).get(protocol_id, 0.5)
                
                # Apply learning rate
                learning_rate = 0.1
                new_capability = current_capability + learning_rate * (performance_score - current_capability)
                
                # Register updated capability
                self.register_model_protocol_capability(
                    model_id=model_id,
                    protocol_id=protocol_id,
                    capability_score=new_capability
                )
                
                logger.info(f"Updated protocol capability for {model_id} on {protocol_id}: {current_capability} -> {new_capability}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to record protocol performance: {str(e)}")
            return False
    
    def get_protocol_capability_summary(self) -> Dict[str, Any]:
        """
        Get a summary of protocol capabilities across models
        
        Returns:
            Summary dictionary
        """
        # Collect all protocols
        all_protocols = set()
        for capabilities in self.protocol_capabilities.values():
            all_protocols.update(capabilities.keys())
        
        # Find top model for each protocol
        top_models = {}
        for protocol_id in all_protocols:
            best_model, score = self.find_best_model_for_protocol(protocol_id)
            if best_model:
                top_models[protocol_id] = {
                    'model_id': best_model,
                    'capability_score': score
                }
        
        # Prepare summary
        return {
            'protocol_count': len(all_protocols),
            'protocols': list(all_protocols),
            'model_count': len(self.protocol_capabilities),
            'models': list(self.protocol_capabilities.keys()),
            'top_models': top_models
        }

# Initialize singleton
_protocol_capability_manager = None

def get_protocol_capability_manager(model_registry=None, protocol_manager=None) -> ProtocolCapabilityManager:
    """
    Get the singleton instance of the ProtocolCapabilityManager
    
    Args:
        model_registry: Model registry instance
        protocol_manager: Protocol manager instance
        
    Returns:
        ProtocolCapabilityManager instance
    """
    global _protocol_capability_manager
    
    if _protocol_capability_manager is None:
        _protocol_capability_manager = ProtocolCapabilityManager(
            model_registry=model_registry,
            protocol_manager=protocol_manager
        )
    
    return _protocol_capability_manager
