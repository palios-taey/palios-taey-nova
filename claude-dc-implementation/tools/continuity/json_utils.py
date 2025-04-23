"""
Utility functions for handling JSON serialization of complex objects.
Provides custom encoders and decoders for complex data types used in Streamlit.
"""

import json
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

class ComplexJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that handles complex Python objects.
    
    Handles the following types:
    - datetime: Converts to ISO format string
    - bytes, bytearray: Converts to base64 encoded string
    - set: Converts to list
    - Path: Converts to string
    - Objects with a to_dict method: Calls the method
    - Objects with a to_json method: Calls the method
    - Objects with a __dict__ attribute: Uses the __dict__
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"__datetime__": obj.isoformat()}
        elif isinstance(obj, (bytes, bytearray)):
            return {"__bytes__": base64.b64encode(obj).decode('ascii')}
        elif isinstance(obj, set):
            return {"__set__": list(obj)}
        elif isinstance(obj, Path):
            return {"__path__": str(obj)}
        elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return {"__custom__": obj.to_dict(), "__type__": obj.__class__.__name__}
        elif hasattr(obj, 'to_json') and callable(getattr(obj, 'to_json')):
            return {"__custom__": obj.to_json(), "__type__": obj.__class__.__name__}
        elif hasattr(obj, '__dict__'):
            return {"__dict__": obj.__dict__, "__type__": obj.__class__.__name__}
        return super().default(obj)

def decode_complex_json(dct):
    """
    JSON decoder for complex objects encoded by ComplexJSONEncoder.
    
    Restores objects serialized by the encoder:
    - datetime objects
    - bytes, bytearray objects
    - set objects
    - Path objects
    - Custom objects (partial restoration as dictionaries)
    """
    if "__datetime__" in dct:
        return datetime.fromisoformat(dct["__datetime__"])
    elif "__bytes__" in dct:
        return base64.b64decode(dct["__bytes__"].encode('ascii'))
    elif "__set__" in dct:
        return set(dct["__set__"])
    elif "__path__" in dct:
        return Path(dct["__path__"])
    elif "__custom__" in dct and "__type__" in dct:
        # We can only restore this as a dictionary since we 
        # don't have access to the original class
        result = dct["__custom__"]
        result["__original_type__"] = dct["__type__"]
        return result
    elif "__dict__" in dct and "__type__" in dct:
        # We can only restore this as a dictionary since we
        # don't have access to the original class
        result = dct["__dict__"]
        result["__original_type__"] = dct["__type__"]
        return result
    return dct

def calculate_checksum(data: Union[str, bytes, dict, list]) -> str:
    """
    Calculate a SHA256 checksum for the given data.
    
    Args:
        data: The data to calculate the checksum for.
              Can be a string, bytes, dict, or list.
    
    Returns:
        A hex string representation of the SHA256 checksum.
    """
    if isinstance(data, dict) or isinstance(data, list):
        # Convert dictionaries and lists to JSON strings
        data = json.dumps(data, sort_keys=True, cls=ComplexJSONEncoder)
    
    if isinstance(data, str):
        # Convert strings to bytes
        data = data.encode('utf-8')
    
    # Calculate the checksum
    return hashlib.sha256(data).hexdigest()

def serialize_with_checksum(data: Any) -> Dict[str, Any]:
    """
    Serialize data to JSON with a checksum.
    
    Args:
        data: The data to serialize.
    
    Returns:
        A dictionary containing the serialized data and its checksum.
    """
    # Serialize the data
    serialized_data = json.dumps(data, cls=ComplexJSONEncoder)
    
    # Calculate the checksum
    checksum = calculate_checksum(serialized_data)
    
    return {
        "data": serialized_data,
        "checksum": checksum,
        "timestamp": datetime.now().isoformat()
    }

def deserialize_with_checksum(serialized: Dict[str, Any], verify: bool = True) -> Tuple[Any, bool]:
    """
    Deserialize data from JSON with checksum verification.
    
    Args:
        serialized: A dictionary containing the serialized data and its checksum.
        verify: Whether to verify the checksum.
    
    Returns:
        A tuple containing:
            - The deserialized data.
            - A boolean indicating whether the checksum verification passed.
    """
    # Get the serialized data and checksum
    serialized_data = serialized.get("data")
    expected_checksum = serialized.get("checksum")
    
    # Verify the checksum if required
    checksum_valid = True
    if verify and expected_checksum:
        actual_checksum = calculate_checksum(serialized_data)
        checksum_valid = actual_checksum == expected_checksum
    
    # Deserialize the data
    if serialized_data:
        data = json.loads(serialized_data, object_hook=decode_complex_json)
    else:
        data = None
    
    return data, checksum_valid