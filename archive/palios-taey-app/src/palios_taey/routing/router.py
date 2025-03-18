"""
Model Routing for PALIOS-TAEY System

This module handles the intelligent routing of tasks to appropriate AI models
based on model capabilities, task requirements, and historical performance.
"""

import os
import logging
import time
import random
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_MIN_CAPABILITY_SCORE = 0.7

class ModelRouter:
    """
    Self-initializing Model Router for routing tasks to appropriate AI models
    
    Provides functionality for:
    - Selecting the best model for a given task
    - Implementing fallback mechanisms
    - Optimizing for performance and cost
    """
    
    def __init__(self, 
                min_capability_score: float = DEFAULT_MIN_CAPABILITY_SCORE,
                enable_learning: bool = True,
                use_mock: bool = False):
        """
        Initialize the Model Router with robust fallback mechanisms
        
        Args:
            min_capability_score: Minimum capability score for a model to be considered
            enable_learning: Whether to enable learning from task outcomes
            use_mock: Whether to use mock mode
        """
        self.min_capability_score = min_capability_score
        self.enable_learning = enable_learning
        
        # Check environment for mock mode setting
        self.use_mock = use_mock or os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Try to load the model registry with fallbacks
        self.model_registry = None
        try:
            # Import model registry
            from model_registry import get_model_registry
            self.model_registry = get_model_registry()
            logger.info("Model registry initialized for model router")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize model registry, will use mock mode: {e}")
            self.model_registry = self._create_mock_model_registry()
            self.use_mock = True
        
        # Recent routing decisions for learning
        self.recent_decisions = []
        self.max_decisions_history = 100
        
        # Default model assignments for mock mode
        self.default_models = {
            'document_summary': 'claude',
            'code_generation': 'gemini',
            'transcript_processing': 'claude',
            'general': 'default_model'
        }
        
        logger.info(f"Model Router initialized successfully in {'mock' if self.use_mock else 'normal'} mode")
    
    def _create_mock_model_registry(self):
        """Create a mock model registry when the real one is unavailable"""
        class MockModelRegistry:
            def __init__(self, default_models):
                self.default_models = default_models
            
            def find_best_model_for_task(self, task_type, min_capability=None, excluded_models=None):
                # Return a mock model based on task type with default scoring
                excluded_models = excluded_models or []
                
                if task_type in self.default_models and self.default_models[task_type] not in excluded_models:
                    return self.default_models[task_type], 0.9
                elif 'general' in self.default_models and self.default_models['general'] not in excluded_models:
                    return self.default_models['general'], 0.8
                else:
                    # Fallback to a random available model
                    available_models = [model for task, model in self.default_models.items() 
                                      if model not in excluded_models]
                    if available_models:
                        return random.choice(available_models), 0.7
                    else:
                        return 'fallback_model', 0.6
            
            def list_models(self, task_type=None, min_capability=None):
                # Return mock model list
                models = []
                
                # Filter by task type if specified
                if task_type:
                    if task_type in self.default_models:
                        models.append({
                            'model_id': self.default_models[task_type],
                            'capability_score': 0.9,
                            'capabilities': {task_type: 0.9}
                        })
                    
                    # Add some backup models
                    backup_score = 0.8
                    for model_id in self.default_models.values():
                        if model_id != self.default_models.get(task_type):
                            models.append({
                                'model_id': model_id,
                                'capability_score': backup_score,
                                'capabilities': {task_type: backup_score}
                            })
                            backup_score -= 0.1  # Decrease score for subsequent models
                else:
                    # Return all models with capabilities
                    for task_type, model_id in self.default_models.items():
                        # Avoid duplicates
                        if not any(m['model_id'] == model_id for m in models):
                            capabilities = {}
                            for task in self.default_models:
                                if self.default_models[task] == model_id:
                                    capabilities[task] = 0.9
                                else:
                                    capabilities[task] = 0.7
                            
                            models.append({
                                'model_id': model_id,
                                'capabilities': capabilities
                            })
                
                return models
            
            def record_performance(self, model_id, task_type, performance_metrics, learn=True):
                # Just log the performance in mock mode
                logger.debug(f"Mock performance recorded for {model_id} on {task_type}: {performance_metrics}")
                return True
        
        logger.info("Created mock model registry")
        return MockModelRegistry(self.default_models)
    
    def route_task(self, 
                  task: Dict[str, Any], 
                  excluded_models: List[str] = None) -> str:
        """
        Route a task to the most appropriate model with robust fallbacks
        
        Args:
            task: Task data dictionary
            excluded_models: List of model IDs to exclude
            
        Returns:
            Selected model ID
        """
        task_id = task.get('task_id', 'unknown')
        task_type = task.get('task_type', 'general')
        
        logger.info(f"Routing task {task_id} of type {task_type}")
        
        # Check if task already has an assigned model
        if 'assigned_model' in task and task['assigned_model']:
            assigned_model = task['assigned_model']
            
            # Verify that the assigned model is suitable
            if self.model_registry:
                capabilities = self.model_registry.get_model_capabilities(assigned_model) if hasattr(self.model_registry, 'get_model_capabilities') else {}
                if task_type in capabilities and capabilities[task_type] >= self.min_capability_score:
                    logger.info(f"Using pre-assigned model {assigned_model} for task {task_id}")
                    
                    # Record decision for learning
                    self._record_routing_decision(task, assigned_model, "pre_assigned")
                    
                    return assigned_model
        
        # Route based on capabilities or defaults in mock mode
        if self.use_mock and not self.model_registry:
            # Simple mock routing based on task type
            model_id = self.default_models.get(task_type, self.default_models.get('general', 'default_model'))
            
            # Record decision
            self._record_routing_decision(task, model_id, "mock_default")
            
            logger.info(f"Routed task {task_id} to model {model_id} using mock defaults")
            return model_id
        
        # Find best model based on capabilities
        return self._select_best_model(task, excluded_models)
    
    def _select_best_model(self, 
                          task: Dict[str, Any], 
                          excluded_models: List[str] = None) -> str:
        """
        Select the best model for a task based on capabilities and other factors
        
        Args:
            task: Task data dictionary
            excluded_models: List of model IDs to exclude
            
        Returns:
            Selected model ID
        """
        task_id = task.get('task_id', 'unknown')
        task_type = task.get('task_type', 'general')
        excluded_models = excluded_models or []
        
        # Specific task requirements
        requirements = task.get('model_requirements', {})
        min_score = requirements.get('min_capability', self.min_capability_score)
        
        try:
            # Get candidate models
            if not self.model_registry:
                # Fallback to default model if registry not available
                model_id = self.default_models.get(task_type, self.default_models.get('general', 'default_model'))
                logger.warning(f"Model registry not available, using default model {model_id}")
                return model_id
            
            candidates = self.model_registry.list_models(
                task_type=task_type,
                min_capability=min_score
            )
            
            # Filter out excluded models
            if excluded_models:
                candidates = [c for c in candidates if c['model_id'] not in excluded_models]
            
            if not candidates:
                logger.warning(f"No suitable models found for task {task_id} of type {task_type}")
                
                # Try with lower capability threshold as fallback
                fallback_min_score = min_score * 0.8  # 80% of original threshold
                fallback_candidates = self.model_registry.list_models(
                    task_type=task_type,
                    min_capability=fallback_min_score
                )
                
                # Filter out excluded models
                if excluded_models:
                    fallback_candidates = [c for c in fallback_candidates if c['model_id'] not in excluded_models]
                
                if not fallback_candidates:
                    # Last resort fallback to default model
                    default_model = self.default_models.get(task_type, self.default_models.get('general', 'default_model'))
                    logger.error(f"No fallback models found for task {task_id}, using default model {default_model}")
                    
                    # Record decision
                    self._record_routing_decision(task, default_model, "last_resort_default")
                    
                    return default_model
                
                candidates = fallback_candidates
            
            # Apply selection strategy
            selected_model = self._apply_selection_strategy(task, candidates)
            
            # Record decision for learning
            self._record_routing_decision(task, selected_model, "capability_based")
            
            logger.info(f"Selected model {selected_model} for task {task_id}")
            return selected_model
            
        except Exception as e:
            # Handle any unexpected errors with fallback to default model
            logger.error(f"Error selecting model for task {task_id}: {str(e)}")
            default_model = self.default_models.get(task_type, self.default_models.get('general', 'default_model'))
            
            # Record decision
            self._record_routing_decision(task, default_model, "error_fallback")
            
            return default_model
    
    def _apply_selection_strategy(self, 
                                 task: Dict[str, Any], 
                                 candidates: List[Dict[str, Any]]) -> str:
        """
        Apply selection strategy to choose among candidate models
        
        Args:
            task: Task data dictionary
            candidates: List of candidate model info dictionaries
            
        Returns:
            Selected model ID
        """
        # Default to highest capability model
        if not candidates:
            raise ValueError("No candidate models provided")
        
        # Extract specific requirements if any
        requirements = task.get('model_requirements', {})
        prioritize_speed = requirements.get('prioritize_speed', False)
        prioritize_quality = requirements.get('prioritize_quality', False)
        
        # Get performance history
        # In a full implementation, this would analyze historical performance metrics
        # For now, we'll use a simple capability-based approach
        
        if prioritize_quality:
            # Choose the model with highest capability
            candidates.sort(key=lambda c: c['capability_score'], reverse=True)
            return candidates[0]['model_id']
        
        elif prioritize_speed:
            # In a real implementation, we would consider latency metrics
            # For now, just choose a simpler, but still capable model
            if len(candidates) > 1:
                # Use the second-best model if available (assuming it's faster)
                candidates.sort(key=lambda c: c['capability_score'], reverse=True)
                return candidates[1]['model_id']
            else:
                return candidates[0]['model_id']
        
        else:
            # Default strategy: highest capability
            candidates.sort(key=lambda c: c['capability_score'], reverse=True)
            return candidates[0]['model_id']
    
    def _record_routing_decision(self, 
                               task: Dict[str, Any], 
                               selected_model: str,
                               selection_method: str) -> None:
        """
        Record a routing decision for learning
        
        Args:
            task: Task data dictionary
            selected_model: Selected model ID
            selection_method: Method used for selection
        """
        if not self.enable_learning:
            return
        
        # Record decision
        decision = {
            'timestamp': time.time(),
            'task_id': task.get('task_id', 'unknown'),
            'task_type': task.get('task_type', 'general'),
            'selected_model': selected_model,
            'selection_method': selection_method
        }
        
        self.recent_decisions.append(decision)
        
        # Limit history size
        if len(self.recent_decisions) > self.max_decisions_history:
            self.recent_decisions = self.recent_decisions[-self.max_decisions_history:]
    
    def record_execution_result(self, 
                               task: Dict[str, Any], 
                               model_id: str,
                               result: Dict[str, Any]) -> None:
        """
        Record execution result for learning
        
        Args:
            task: Task data dictionary
            model_id: Model ID that executed the task
            result: Execution result
        """
        if not self.enable_learning or not self.model_registry:
            return
        
        task_id = task.get('task_id', 'unknown')
        task_type = task.get('task_type', 'general')
        
        try:
            # Extract metrics from result
            success = result.get('status') == 'completed'
            execution_time = None
            
            if 'started_at' in task and 'completed_at' in result:
                try:
                    from datetime import datetime
                    start_time = datetime.fromisoformat(task['started_at'])
                    end_time = datetime.fromisoformat(result['completed_at'])
                    execution_time = (end_time - start_time).total_seconds()
                except (ValueError, TypeError):
                    pass
            
            # Metrics for learning
            metrics = {
                'success': success,
                'execution_time': execution_time,
                'error_count': 0 if success else 1
            }
            
            # Quality metrics if available
            if 'quality_score' in result:
                metrics['quality'] = result['quality_score']
            
            # Efficiency metrics
            if execution_time is not None:
                # Lower time is better, so inverse relationship with efficiency
                # normalized to 0-1 range, assuming reasonable execution time range
                base_efficiency = 1.0 - min(1.0, execution_time / 60.0)  # Normalize assuming 60s is long
                metrics['efficiency'] = base_efficiency
            
            # Record performance if model registry is available
            if hasattr(self.model_registry, 'record_performance'):
                self.model_registry.record_performance(
                    model_id=model_id,
                    task_type=task_type,
                    performance_metrics=metrics,
                    learn=self.enable_learning
                )
            
            logger.debug(f"Recorded execution result for task {task_id} with model {model_id}")
        except Exception as e:
            logger.error(f"Error recording execution result: {str(e)}")
    
    def get_model_suggestions(self, task_type: str, count: int = 3) -> List[Dict[str, Any]]:
        """
        Get model suggestions for a task type with fallbacks
        
        Args:
            task_type: Type of task
            count: Number of suggestions to return
            
        Returns:
            List of model suggestions
        """
        try:
            # Use model registry if available
            if self.model_registry and hasattr(self.model_registry, 'list_models'):
                # Get models capable of handling this task type
                models = self.model_registry.list_models(
                    task_type=task_type,
                    min_capability=self.min_capability_score
                )
                
                # Sort by capability score
                models.sort(key=lambda m: m['capability_score'], reverse=True)
                
                # Return top N models
                suggestions = []
                for i, model in enumerate(models[:count]):
                    suggestions.append({
                        'model_id': model['model_id'],
                        'capability_score': model['capability_score'],
                        'recommendation_reason': f"Ranked #{i+1} for {task_type} tasks"
                    })
                
                return suggestions
            else:
                # Fallback to mock suggestions using default models
                suggestions = []
                
                # Add default model for this task type first
                if task_type in self.default_models:
                    suggestions.append({
                        'model_id': self.default_models[task_type],
                        'capability_score': 0.9,
                        'recommendation_reason': f"Optimized for {task_type} tasks"
                    })
                
                # Fill with other default models
                used_models = set()
                if suggestions:
                    used_models.add(suggestions[0]['model_id'])
                
                for other_type, model_id in self.default_models.items():
                    if model_id not in used_models and len(suggestions) < count:
                        suggestions.append({
                            'model_id': model_id,
                            'capability_score': 0.8 if other_type == 'general' else 0.7,
                            'recommendation_reason': f"Compatible with {task_type} tasks"
                        })
                        used_models.add(model_id)
                
                return suggestions
        except Exception as e:
            logger.error(f"Error getting model suggestions: {str(e)}")
            # Fallback to single default model suggestion
            return [{
                'model_id': self.default_models.get(task_type, self.default_models.get('general', 'default_model')),
                'capability_score': 0.7,
                'recommendation_reason': f"Default model for {task_type} tasks"
            }]

    def analyze_routing_efficiency(self) -> Dict[str, Any]:
        """
        Analyze routing efficiency based on recent decisions
        
        Returns:
            Analysis results
        """
        if not self.recent_decisions:
            return {
                'status': 'no_data',
                'message': 'No routing decisions recorded yet'
            }
        
        # Count decisions by model and task type
        model_counts = {}
        type_counts = {}
        method_counts = {}
        
        for decision in self.recent_decisions:
            model_id = decision['selected_model']
            task_type = decision['task_type']
            method = decision['selection_method']
            
            model_counts[model_id] = model_counts.get(model_id, 0) + 1
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Calculate diversity metrics
        total_decisions = len(self.recent_decisions)
        model_diversity = len(model_counts) / total_decisions if total_decisions > 0 else 0
        
        # Create most used models list
        most_used_models = sorted(
            [(model, count) for model, count in model_counts.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'total_decisions': total_decisions,
            'unique_models_used': len(model_counts),
            'unique_task_types': len(type_counts),
            'model_diversity_score': model_diversity,
            'most_used_models': most_used_models[:3],
            'task_type_distribution': type_counts,
            'selection_method_distribution': method_counts
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the model router
        
        Returns:
            Status information
        """
        return {
            "status": "active",
            "mode": "mock" if self.use_mock else "normal",
            "model_registry_available": self.model_registry is not None,
            "learning_enabled": self.enable_learning,
            "min_capability_score": self.min_capability_score,
            "recent_decisions_count": len(self.recent_decisions)
        }

# Singleton instance
_model_router_instance = None

def get_model_router(
    min_capability_score: float = DEFAULT_MIN_CAPABILITY_SCORE,
    use_mock: bool = False
) -> ModelRouter:
    """
    Get the singleton instance of the ModelRouter
    
    Args:
        min_capability_score: Minimum capability score
        use_mock: Whether to use mock mode
        
    Returns:
        ModelRouter instance
    """
    global _model_router_instance
    
    if _model_router_instance is None:
        # Check environment for mock mode
        env_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        use_mock = use_mock or env_mock
        
        _model_router_instance = ModelRouter(
            min_capability_score=min_capability_score,
            use_mock=use_mock
        )
    
    return _model_router_instance