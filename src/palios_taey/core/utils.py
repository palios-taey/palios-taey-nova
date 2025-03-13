"""Utility functions for PALIOS-TAEY."""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        A unique ID string
    """
    uuid_str = str(uuid.uuid4())
    return f"{prefix}{uuid_str}" if prefix else uuid_str


def to_json(obj: Any) -> str:
    """
    Convert an object to a JSON string.
    
    Args:
        obj: The object to convert
        
    Returns:
        A JSON string representation of the object
    """
    def default_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)
    
    return json.dumps(obj, default=default_serializer)


def from_json(json_str: str) -> Any:
    """
    Convert a JSON string to an object.
    
    Args:
        json_str: The JSON string to convert
        
    Returns:
        The object represented by the JSON string
    """
    return json.loads(json_str)


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: The first dictionary
        dict2: The second dictionary
        
    Returns:
        A new dictionary with the merged contents
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
