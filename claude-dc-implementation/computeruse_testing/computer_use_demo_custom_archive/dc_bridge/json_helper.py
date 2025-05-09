"""
Helper for JSON serialization.
"""

import json
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that can handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_serialize(obj):
    """Serialize an object to a JSON string."""
    return json.dumps(obj, cls=CustomJSONEncoder, indent=2)