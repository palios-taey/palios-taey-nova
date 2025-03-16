import os
import secrets
from functools import wraps
from flask import request, jsonify

API_KEYS = {
    "test_key": "development"
}

def generate_api_key():
    return secrets.token_urlsafe(32)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key in API_KEYS:
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated_function
