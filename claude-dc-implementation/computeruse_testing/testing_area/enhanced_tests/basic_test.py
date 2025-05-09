#!/usr/bin/env python3
"""
Basic test for the api_response_callback NoneType fix.
This is a simple script that directly tests the callback with None request.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Now we can import from enhanced_tests
from enhanced_tests.mock_streamlit import MockStreamlit

def main():
    """Run the basic test."""
    print("=" * 80)
    print("TESTING NoneType ERROR FIX IN API RESPONSE CALLBACK")
    print("=" * 80)
    print("This test verifies that api_response_callback can handle None request parameter")
    print("which was causing an AttributeError in the original implementation.")
    print("=" * 80)
    
    # Disable logging to keep output clean
    import logging
    logging.getLogger('mock_streamlit').setLevel(logging.CRITICAL)
    
    # Create test objects
    mock_st = MockStreamlit()
    
    print("TEST 1: Testing api_response_callback with None request parameter...")
    mock_st.api_response_callback(None, {"test": "response"}, None)
    
    # Check if there were any errors
    if mock_st.errors:
        print("  RESULT: FAILED! Errors detected:")
        for error in mock_st.errors:
            print(f"  - {error}")
    else:
        print("  RESULT: PASSED! No errors detected.")
        print("  This confirms the fix for AttributeError: 'NoneType' object has no attribute 'method'")
    
    print("\nTEST 2: Testing api_response_callback with error parameter...")
    test_error = Exception("Test error")
    mock_st.api_response_callback(None, None, test_error)
    
    # Verify the error was recorded properly
    if len(mock_st.api_responses) > 0 and mock_st.api_responses[1]['error'] == test_error:
        print("  RESULT: PASSED! Error was properly handled.")
    else:
        print("  RESULT: FAILED! Error handling is not working correctly.")
    
if __name__ == "__main__":
    main()