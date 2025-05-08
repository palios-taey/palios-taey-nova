"""
Simple script to verify the API key is valid.
"""

import os
import json
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("check_api_key")

async def check_api():
    # Load the API key from the correct secrets file
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    
    if not os.path.exists(secrets_path):
        logger.error(f"Secrets file not found at {secrets_path}")
        return
    
    try:
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            api_key = secrets["api_keys"]["anthropic"]
            
            # Show first few characters for verification
            logger.info(f"Loaded API key (first 10 chars): {api_key[:10]}...")
            
            # Import Anthropic client
            from anthropic import AsyncAnthropic
            
            # Create client
            client = AsyncAnthropic(api_key=api_key)
            
            # Test the API with a simple query
            response = await client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello Claude, this is a simple API test. Respond with 'API test successful!' and nothing else."}]
            )
            
            logger.info(f"API Response: {response.content[0].text}")
            print(f"\nAPI Response: {response.content[0].text}")
            
            if "API test successful" in response.content[0].text:
                logger.info("✅ API key is valid and working correctly")
                print("\n✅ API key is valid and working correctly")
                return True
            else:
                logger.warning("⚠️ API response received but not as expected")
                print("\n⚠️ API response received but not as expected")
                return False
    
    except Exception as e:
        logger.error(f"Error testing API key: {str(e)}")
        print(f"\n❌ Error testing API key: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(check_api())