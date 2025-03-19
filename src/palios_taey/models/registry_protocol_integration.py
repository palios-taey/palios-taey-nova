"""
Registry Protocol Integration module for PALIOS-TAEY

This module integrates the protocol capabilities into the model registry.
"""

def integrate_protocol_capabilities(model_registry, protocol_capability_manager):
    """
    Integrate protocol capabilities into model registry
    
    Args:
        model_registry: Model registry instance
        protocol_capability_manager: Protocol capability manager instance
    """
    # Get all models from registry
    models = model_registry.list_models()
    
    # Get all protocol capabilities
    for model in models:
        model_id = model.get('model_id', '')
        
        # Get protocol capabilities for this model
        protocol_capabilities = protocol_capability_manager.get_model_protocol_capabilities(model_id)
        
        # Register each protocol capability as a task type
        for protocol_id, capability_score in protocol_capabilities.items():
            model_registry.update_capability(
                model_id=model_id,
                task_type=f"protocol_{protocol_id}",
                new_score=capability_score
            )
    
    # Update model registry capability summary
    model_registry.self_optimize()
