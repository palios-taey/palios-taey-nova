"""
Simple API test to verify the API key is working correctly.
"""

import os
import json
import asyncio
import logging
from anthropic import AsyncAnthropic
from feature_toggles import get_feature_toggles, get_feature_setting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_test")

# Load API key from secrets file
def load_api_key():
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    try:
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            return secrets["api_keys"]["anthropic"]
    except Exception as e:
        logger.error(f"Error loading API key: {str(e)}")
        return None

async def test_api():
    """Test the API key by making a simple request."""
    api_key = load_api_key()
    
    if not api_key:
        logger.error("API key not found or invalid")
        return False
    
    client = AsyncAnthropic(api_key=api_key)
    
    # Get model from feature toggles
    model = get_feature_setting("api_model", "claude-3-7-sonnet-20250219")
    
    try:
        logger.info(f"Testing API key with model {model}...")
        response = await client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello Claude, can you hear me?"}]
        )
        
        logger.info(f"API response: {response.content[0].text}")
        logger.info("API test successful!")
        return True
    
    except Exception as e:
        logger.error(f"API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_api())
    if success:
        print("✅ API key is valid and working correctly")
    else:
        print("❌ API key test failed")