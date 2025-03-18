"""
Dynamic Model Registry for PALIOS-TAEY System

This module implements a learning-based capability discovery system that allows
models to advertise and update their own capabilities, enabling optimal task routing.
"""

import os
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default capability thresholds
DEFAULT_CAPABILITY_THRESHOLD = 0.7

class ModelRegistry:
    """
    Dynamic Model Registry for managing model capabilities
    
    Provides functionality for:
    - Registering models and their capabilities
    - Updating capabilities based on execution results
    - Finding optimal models for specific task types
    - Learning from execution outcomes to improve routing
    """
    
    def __init__(self, 
                 config_dir: str = "config/model_capabilities",
                 learning_rate: float = 0.05,
                 capability_threshold: float = DEFAULT_CAPABILITY_THRESHOLD):
        """
        Initialize the Model Registry
        
        Args:
            config_dir: Directory for model capability configurations
            learning_rate: Rate at which to update capabilities from performance
            capability_threshold: Minimum capability score to be considered capable
        """
        self.config_dir = config_dir
        self.learning_rate = learning_rate
        self.capability_threshold = capability_threshold
        
        # Model capability registry
        self.model_capabilities = {}
        
        # Performance history for learning
        self.performance_history = {}
        
        # Use mock mode if specified
        self.use_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Initialize from configuration files
        self._initialize_from_config()
        
        logger.info("Model Registry initialized successfully")
    
    def _initialize_default_models(self):
        """Initialize with default models when config is not available"""
        logger.warning("Initializing model registry with default models")
        
        # Add default models
        self.model_capabilities = {
            "gemini": {
                "document_summary": 0.9,
                "code_generation": 0.85,
                "general": 0.95
            },
            "claude": {
                "document_summary": 0.95,
                "transcript_processing": 0.9,
                "general": 0.92
            },
            "openai": {
                "document_summary": 0.88,
                "code_generation": 0.92,
                "general": 0.90
            }
        }
        
        # Initialize performance history
        for model_id in self.model_capabilities:
            self.performance_history[model_id] = {}
        
        # Save default models in config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir, exist_ok=True)
                for model_id, capabilities in self.model_capabilities.items():
                    model_path = os.path.join(self.config_dir, f"{model_id}.json")
                    with open(model_path, 'w') as f:
                        json.dump(capabilities, f, indent=2)
                logger.info("Created default model capability files")
            except Exception as e:
                logger.error(f"Failed to create default model files: {str(e)}")
        
        logger.info("Default model capabilities initialized")
    
    def _initialize_from_config(self):
        """Initialize model capabilities from configuration files"""
        try:
            if self.use_mock:
                logger.info("Mock mode enabled, using default models")
                self._initialize_default_models()
                return
                
            if not os.path.exists(self.config_dir):
                logger.warning(f"Config directory not found: {self.config_dir}")
                os.makedirs(self.config_dir, exist_ok=True)
                self._initialize_default_models()  # Fall back to defaults
                return
            
            # Check if directory is empty
            if not os.listdir(self.config_dir):
                logger.warning(f"Config directory is empty: {self.config_dir}")
                self._initialize_default_models()  # Fall back to defaults
                return
            
            # Load all JSON files in the config directory
            loaded_any = False
            for filename in os.listdir(self.config_dir):
                if not filename.endswith('.json'):
                    continue
                
                model_id = filename.replace('.json', '')
                filepath = os.path.join(self.config_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        capabilities = json.load(f)
                    
                    self.model_capabilities[model_id] = capabilities
                    logger.debug(f"Loaded capabilities for model: {model_id}")
                    loaded_any = True
                except Exception as e:
                    logger.error(f"Failed to load capabilities for {model_id}: {str(e)}")
            
            # If no files were loaded successfully, initialize with defaults
            if not loaded_any:
                self._initialize_default_models()
        except Exception as e:
            logger.error(f"Error initializing from config: {str(e)}")
            self._initialize_default_models()  # Fall back to defaults
    
    def register_model(self, 
                      model_id: str, 
                      capabilities: Dict[str, float],
                      persist: bool = True) -> bool:
        """
        Register a new model with its capabilities
        
        Args:
            model_id: Unique identifier for the model
            capabilities: Dictionary mapping task types to capability scores (0.0-1.0)
            persist: Whether to persist the capabilities to disk
            
        Returns:
            Whether registration was successful
        """
        logger.info(f"Registering model: {model_id}")
        
        # Validate capabilities
        validated_capabilities = {}
        for task_type, score in capabilities.items():
            # Ensure score is within valid range
            validated_score = min(1.0, max(0.0, float(score)))
            validated_capabilities[task_type] = validated_score
        
        # Add to registry
        self.model_capabilities[model_id] = validated_capabilities
        
        # Initialize performance history
        if model_id not in self.performance_history:
            self.performance_history[model_id] = {}
        
        # Persist to disk if requested
        if persist:
            return self._persist_capabilities(model_id)
        
        return True
    
    def _persist_capabilities(self, model_id: str) -> bool:
        """
        Persist model capabilities to disk
        
        Args:
            model_id: Model identifier
            
        Returns:
            Whether persistence was successful
        """
        if model_id not in self.model_capabilities:
            logger.warning(f"Cannot persist capabilities for unknown model: {model_id}")
            return False
        
        filepath = os.path.join(self.config_dir, f"{model_id}.json")
        
        try:
            # Ensure directory exists
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Write capabilities
            with open(filepath, 'w') as f:
                json.dump(self.model_capabilities[model_id], f, indent=2)
            
            logger.debug(f"Persisted capabilities for model: {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to persist capabilities for {model_id}: {str(e)}")
            return False
    
    def update_capability(self, 
                         model_id: str, 
                         task_type: str, 
                         new_score: float,
                         persist: bool = True) -> bool:
        """
        Update a specific capability for a model
        
        Args:
            model_id: Model identifier
            task_type: Type of task
            new_score: New capability score (0.0-1.0)
            persist: Whether to persist the updated capabilities
            
        Returns:
            Whether update was successful
        """
        if model_id not in self.model_capabilities:
            logger.warning(f"Cannot update capability for unknown model: {model_id}")
            return False
        
        # Ensure score is within valid range
        validated_score = min(1.0, max(0.0, float(new_score)))
        
        # Update capability
        self.model_capabilities[model_id][task_type] = validated_score
        logger.info(f"Updated {model_id} capability for {task_type} to {validated_score}")
        
        # Persist if requested
        if persist:
            return self._persist_capabilities(model_id)
        
        return True
    
    def record_performance(self, 
                          model_id: str, 
                          task_type: str, 
                          performance_metrics: Dict[str, Any],
                          learn: bool = True) -> bool:
        """
        Record performance metrics for a model's execution of a task
        
        Args:
            model_id: Model identifier
            task_type: Type of task
            performance_metrics: Dictionary of performance metrics
            learn: Whether to update capabilities based on performance
            
        Returns:
            Whether recording was successful
        """
        if model_id not in self.performance_history:
            self.performance_history[model_id] = {}
        
        if task_type not in self.performance_history[model_id]:
            self.performance_history[model_id][task_type] = []
        
        # Add timestamp to metrics
        metrics_with_time = performance_metrics.copy()
        metrics_with_time['timestamp'] = datetime.now().isoformat()
        
        # Add to history
        self.performance_history[model_id][task_type].append(metrics_with_time)
        
        # Limit history size
        max_history = 100
        if len(self.performance_history[model_id][task_type]) > max_history:
            self.performance_history[model_id][task_type] = self.performance_history[model_id][task_type][-max_history:]
        
        # Learn from performance if requested
        if learn:
            self._learn_from_performance(model_id, task_type, performance_metrics)
        
        return True
    
    def _learn_from_performance(self, 
                               model_id: str, 
                               task_type: str, 
                               metrics: Dict[str, Any]) -> None:
        """
        Update model capabilities based on performance metrics
        
        Args:
            model_id: Model identifier
            task_type: Type of task
            metrics: Performance metrics
        """
        if model_id not in self.model_capabilities:
            logger.warning(f"Cannot learn for unknown model: {model_id}")
            return
        
        # Get current capability score
        current_score = self.model_capabilities[model_id].get(task_type, 0.5)
        
        # Calculate performance score (normalized to 0.0-1.0)
        performance_score = self._calculate_performance_score(metrics)
        
        # Update capability with learning rate
        new_score = current_score + (self.learning_rate * (performance_score - current_score))
        new_score = min(1.0, max(0.0, new_score))
        
        # Update capability
        self.update_capability(model_id, task_type, new_score, persist=True)
        
        logger.debug(f"Learned capability update for {model_id} on {task_type}: {current_score} -> {new_score}")
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate a normalized performance score from metrics
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Normalized performance score (0.0-1.0)
        """
        # Extract key metrics with defaults
        success = metrics.get('success', False)
        quality = metrics.get('quality', 0.5)
        efficiency = metrics.get('efficiency', 0.5)
        error_count = metrics.get('error_count', 0)
        
        # Calculate base score from success/failure
        base_score = 0.7 if success else 0.3
        
        # Adjust based on quality and efficiency
        score = base_score * 0.4 + quality * 0.4 + efficiency * 0.2
        
        # Penalize for errors
        error_penalty = min(0.5, error_count * 0.1)
        score = max(0.0, score - error_penalty)
        
        return score
    
    def find_best_model_for_task(self, 
                                task_type: str, 
                                min_capability: Optional[float] = None,
                                excluded_models: List[str] = None) -> Tuple[Optional[str], float]:
        """
        Find the best model for a specific task type
        
        Args:
            task_type: Type of task
            min_capability: Minimum capability score required (uses default if None)
            excluded_models: List of model IDs to exclude
            
        Returns:
            Tuple of (best_model_id, capability_score) or (None, 0.0) if no suitable model
        """
        if min_capability is None:
            min_capability = self.capability_threshold
        
        if excluded_models is None:
            excluded_models = []
        
        best_model = None
        best_score = 0.0
        
        # If no models are registered yet and we're using mock mode, add some defaults
        if not self.model_capabilities and self.use_mock:
            self._initialize_default_models()
        
        for model_id, capabilities in self.model_capabilities.items():
            # Skip excluded models
            if model_id in excluded_models:
                continue
            
            # Check if model can handle this task type
            score = capabilities.get(task_type, 0.0)
            
            # If no explicit capability for this task type, check for general capability
            if score == 0.0 and 'general' in capabilities:
                score = capabilities['general'] * 0.8  # Slightly lower confidence for general tasks
            
            # Check if it meets minimum capability
            if score < min_capability:
                continue
            
            # Check if it's better than current best
            if score > best_score:
                best_model = model_id
                best_score = score
        
        # If still no suitable model found, default to first available model in mock mode
        if best_model is None and self.use_mock and self.model_capabilities:
            # Use the first model as a fallback
            best_model = next(iter(self.model_capabilities.keys()))
            best_score = 0.7  # Default score
            logger.warning(f"No suitable model found for {task_type}, using fallback model {best_model}")
        
        return (best_model, best_score)
    
    def get_model_capabilities(self, model_id: str) -> Dict[str, float]:
        """
        Get capabilities for a specific model
        
        Args:
            model_id: Model identifier
            
        Returns:
            Dictionary of capabilities or empty dict if model not found
        """
        return self.model_capabilities.get(model_id, {})
    
    def list_models(self, 
                   task_type: Optional[str] = None, 
                   min_capability: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        List all registered models, optionally filtered by task type
        
        Args:
            task_type: Optional task type to filter by
            min_capability: Minimum capability score required (uses default if None)
            
        Returns:
            List of model information dictionaries
        """
        if min_capability is None:
            min_capability = self.capability_threshold
        
        # If no models are registered yet and we're using mock mode, add some defaults
        if not self.model_capabilities and self.use_mock:
            self._initialize_default_models()
        
        result = []
        
        for model_id, capabilities in self.model_capabilities.items():
            # If filtering by task type
            if task_type:
                score = capabilities.get(task_type, 0.0)
                
                # If no explicit capability for this task type, check for general capability
                if score == 0.0 and 'general' in capabilities:
                    score = capabilities['general'] * 0.8  # Slightly lower confidence for general tasks
                
                if score < min_capability:
                    continue
                
                result.append({
                    'model_id': model_id,
                    'capability_score': score,
                    'capabilities': capabilities
                })
            else:
                # Include all models
                result.append({
                    'model_id': model_id,
                    'capabilities': capabilities
                })
        
        # Sort by capability score if task_type is provided
        if task_type:
            result.sort(key=lambda x: x['capability_score'], reverse=True)
        
        return result
    
    def get_capability_summary(self) -> Dict[str, Any]:
        """
        Get a summary of model capabilities across all task types
        
        Returns:
            Summary dictionary
        """
        # If no models are registered yet and we're using mock mode, add some defaults
        if not self.model_capabilities and self.use_mock:
            self._initialize_default_models()
            
        summary = {
            'model_count': len(self.model_capabilities),
            'task_types': set(),
            'top_models': {}
        }
        
        # Collect all task types
        for capabilities in self.model_capabilities.values():
            summary['task_types'].update(capabilities.keys())
        
        # Find top model for each task type
        for task_type in summary['task_types']:
            best_model, score = self.find_best_model_for_task(task_type)
            if best_model:
                summary['top_models'][task_type] = {
                    'model_id': best_model,
                    'capability_score': score
                }
        
        # Convert task_types to list for JSON serialization
        summary['task_types'] = list(summary['task_types'])
        
        return summary

    def discover_capabilities(self, 
                            model_id: str, 
                            test_task_types: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Discover model capabilities through testing
        
        Args:
            model_id: Model identifier
            test_task_types: List of task types to test (uses all known if None)
            
        Returns:
            Dictionary of discovered capabilities
        """
        logger.info(f"Discovering capabilities for model: {model_id}")
        
        # Use existing task types if none provided
        if test_task_types is None:
            # Collect all known task types from all models
            test_task_types = set()
            for capabilities in self.model_capabilities.values():
                test_task_types.update(capabilities.keys())
            test_task_types = list(test_task_types)
        
        # Get current capabilities as starting point
        current_capabilities = self.get_model_capabilities(model_id)
        discovered_capabilities = current_capabilities.copy()
        
        # In a real implementation, we would use a separate TestDriver
        # to execute test tasks and measure performance.
        # For now, we'll simulate discovery with placeholder values.
        
        for task_type in test_task_types:
            # Skip if already have high confidence in capability
            if task_type in current_capabilities and current_capabilities[task_type] > 0.8:
                continue
                
            # This would be replaced with actual test execution
            # For simulation, we'll assign a random but reasonable score
            # In real world, we would execute test tasks and measure performance
            
            import random
            simulated_score = random.uniform(0.6, 0.95)
            
            # Update discovered capabilities
            discovered_capabilities[task_type] = simulated_score
            
            logger.debug(f"Discovered capability for {model_id} on {task_type}: {simulated_score}")
        
        # Register the discovered capabilities
        self.register_model(model_id, discovered_capabilities, persist=True)
        
        return discovered_capabilities

    def self_optimize(self) -> Dict[str, Any]:
        """
        Perform self-optimization of model registry
        
        This function analyzes performance history and updates model capabilities
        based on actual performance rather than registered capabilities.
        
        Returns:
            Summary of optimization changes
        """
        logger.info("Performing self-optimization of model registry")
        
        changes = {
            'models_updated': 0,
            'capabilities_adjusted': 0,
            'new_capabilities_discovered': 0,
            'details': []
        }
        
        # For each model with performance history
        for model_id, task_histories in self.performance_history.items():
            if model_id not in self.model_capabilities:
                continue
                
            model_changes = {
                'model_id': model_id,
                'adjustments': []
            }
            
            # For each task type with performance history
            for task_type, history in task_histories.items():
                if not history:
                    continue
                
                # Calculate average performance score from recent history
                recent_history = history[-min(10, len(history)):]
                performance_scores = [self._calculate_performance_score(metrics) 
                                     for metrics in recent_history]
                
                if not performance_scores:
                    continue
                    
                avg_performance = sum(performance_scores) / len(performance_scores)
                
                # Get current capability
                current_capability = self.model_capabilities[model_id].get(task_type, 0.0)
                
                # Calculate difference
                diff = avg_performance - current_capability
                
                # Only adjust if significant difference
                if abs(diff) < 0.05:
                    continue
                
                # Update capability
                self.update_capability(model_id, task_type, avg_performance, persist=False)
                
                # Record adjustment
                model_changes['adjustments'].append({
                    'task_type': task_type,
                    'old_score': current_capability,
                    'new_score': avg_performance,
                    'difference': diff
                })
                
                changes['capabilities_adjusted'] += 1
                
                # Record if this is a new capability
                if current_capability == 0.0 and avg_performance > self.capability_threshold:
                    changes['new_capabilities_discovered'] += 1
            
            # Add model changes if any adjustments were made
            if model_changes['adjustments']:
                changes['models_updated'] += 1
                changes['details'].append(model_changes)
                
                # Persist updated capabilities
                self._persist_capabilities(model_id)
        
        logger.info(f"Self-optimization complete. Updated {changes['models_updated']} models.")
        return changes

# Singleton instance for global access
_model_registry_instance = None

def get_model_registry(config_dir: str = "config/model_capabilities") -> ModelRegistry:
    """
    Get the singleton instance of the ModelRegistry
    
    Args:
        config_dir: Configuration directory
        
    Returns:
        ModelRegistry instance
    """
    global _model_registry_instance
    
    if _model_registry_instance is None:
        _model_registry_instance = ModelRegistry(config_dir=config_dir)
        
    return _model_registry_instance