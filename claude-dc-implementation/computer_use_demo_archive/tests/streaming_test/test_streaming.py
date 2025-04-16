"""
Test script for streaming functionality
"""
import sys
import os

# Add the computer_use_demo directory to the path
sys.path.append('/home/computeruse/computer_use_demo')

def test_streaming_client():
    """Test the streaming client module"""
    try:
        from streaming.streaming_client import StreamingClient
        print("✅ StreamingClient imports successfully")
        
        # Don't create an actual client, just verify the class exists
        print("StreamingClient class attributes:")
        for attr in dir(StreamingClient):
            if not attr.startswith('__'):
                print(f"  - {attr}")
        
        return True
    except Exception as e:
        print(f"❌ StreamingClient test failed: {e}")
        return False

def test_streaming_integration():
    """Test if loop.py properly integrates streaming"""
    try:
        # Look for streaming imports in loop.py
        with open('/home/computeruse/computer_use_demo/tests/streaming_test/loop.py', 'r') as f:
            loop_content = f.read()
        
        if 'streaming' in loop_content:
            print("✅ loop.py contains streaming references")
            print("Streaming references in loop.py:")
            
            # Find lines with streaming
            lines = loop_content.split('\n')
            for i, line in enumerate(lines):
                if 'streaming' in line:
                    print(f"  Line {i+1}: {line.strip()}")
        else:
            print("❌ loop.py does not contain streaming references")
        
        # Check if streamlit.py uses streaming
        with open('/home/computeruse/computer_use_demo/tests/streaming_test/streamlit.py', 'r') as f:
            streamlit_content = f.read()
        
        if 'streaming' in streamlit_content:
            print("✅ streamlit.py contains streaming references")
            print("Streaming references in streamlit.py:")
            
            # Find lines with streaming
            lines = streamlit_content.split('\n')
            for i, line in enumerate(lines):
                if 'streaming' in line:
                    print(f"  Line {i+1}: {line.strip()}")
        else:
            print("❌ streamlit.py does not contain streaming references")
        
        return 'streaming' in loop_content and 'streaming' in streamlit_content
    except Exception as e:
        print(f"❌ Streaming integration test failed: {e}")
        return False

def run_all_tests():
    """Run all streaming tests"""
    test_results = {
        "streaming_client": test_streaming_client(),
        "streaming_integration": test_streaming_integration()
    }
    
    print("\n=== Streaming Test Results ===")
    for test, result in test_results.items():
        print(f"{test}: {'✅ PASS' if result else '❌ FAIL'}")
    
    all_passed = all(test_results.values())
    print(f"\nOverall: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    print("Starting streaming functionality tests...")
    success = run_all_tests()
    
    if not success:
        print("\nRecommendation: Streaming support needs to be properly implemented in loop.py and streamlit.py")