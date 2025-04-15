"""
Test streaming functionality
"""
import sys
import os

# Add the test directory to path
sys.path.insert(0, '/home/computeruse/computer_use_demo/tests/streaming_complete')

# Import modules from test environment
try:
    from streaming.streaming_client import StreamingClient
    from token_management.token_manager import TokenManager
    token_manager = TokenManager()
    print("✅ Successfully imported core modules")
except Exception as e:
    print(f"❌ Failed to import core modules: {e}")
    sys.exit(1)

def test_streaming_client():
    """Test the streaming client initialization"""
    try:
        # Create a client instance (without making real API calls)
        client = StreamingClient(token_manager=token_manager)
        print(f"✅ StreamingClient initialized successfully")
        
        # Check available methods
        methods = [method for method in dir(client) if not method.startswith('_') and callable(getattr(client, method))]
        print(f"Available methods: {', '.join(methods)}")
        
        return True
    except Exception as e:
        print(f"❌ StreamingClient initialization failed: {e}")
        return False

def test_streaming_integration():
    """Test if streaming is properly integrated in loop.py and streamlit.py"""
    success = True
    
    # Check loop.py integration
    try:
        with open('loop.py', 'r') as f:
            loop_content = f.read()
        
        # Look for streaming imports and usage
        if 'from streaming' in loop_content and 'StreamingClient' in loop_content:
            print("✅ loop.py properly imports streaming module")
        else:
            print("❌ loop.py does not properly import streaming module")
            success = False
        
        # Look for streaming client usage
        if 'streaming_client' in loop_content.lower() or 'streamingclient' in loop_content.lower():
            print("✅ loop.py uses streaming client")
        else:
            print("❌ loop.py does not use streaming client")
            success = False
    except Exception as e:
        print(f"❌ loop.py check failed: {e}")
        success = False
    
    # Check streamlit.py integration
    try:
        with open('streamlit.py', 'r') as f:
            streamlit_content = f.read()
        
        # Look for streaming references
        if 'streaming' in streamlit_content:
            print("✅ streamlit.py contains streaming references")
        else:
            print("❌ streamlit.py does not contain streaming references")
            success = False
        
        # Check for f-string syntax issues (a common error)
        if "}[" in streamlit_content or "]{" in streamlit_content:
            print("❌ WARNING: Possible f-string syntax issues in streamlit.py")
            success = False
    except Exception as e:
        print(f"❌ streamlit.py check failed: {e}")
        success = False
    
    return success

if __name__ == "__main__":
    print("Testing streaming functionality...")
    client_test = test_streaming_client()
    integration_test = test_streaming_integration()
    
    if client_test and integration_test:
        print("\n✅ All streaming tests passed")
    else:
        print("\n❌ Some streaming tests failed - fix before deployment")
        sys.exit(1)