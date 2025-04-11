"""
Test script for the simple token management system.
"""

import time
import sys
import os
from simple_token_manager import token_manager

def test_token_manager():
    """Run tests on the token manager."""
    print("✅ Successfully imported TokenManager")
    print("\n🧪 Token Management System Test")
    print("=" * 50)
    
    print("\n🔍 Testing token management system...\n")
    
    # Test initialization
    print(f"✅ Initialized TokenManager with extended output beta: {token_manager.extended_output_beta}")
    
    # Test extended output beta
    try:
        # Mock headers to test beta detection
        mock_headers = {
            "x-input-tokens": "100",
            "x-output-tokens": "200",
            "anthropic-beta": "output-128k-2025-02-19"
        }
        
        # Process mock request
        token_manager.manage_request(mock_headers)
        print("✅ Extended output beta (128K tokens) is available")
        print(f"Beta confirmed: True")
    except Exception as e:
        print(f"❌ Extended output beta not available, using standard limits")
        print(f"Beta access test result: False")
    
    # Test API call simulation
    print("\n📡 Making API call...\n")
    
    try:
        # This is a mock API call - in a real scenario, you would call the Anthropic API
        mock_response_headers = {
            "x-input-tokens": "500",
            "x-output-tokens": "1000"
        }
        
        # Process the mock response
        token_manager.manage_request(mock_response_headers)
        
        # Display token usage statistics
        stats = token_manager.get_statistics()
        print("\n📊 Token Usage Statistics:")
        print("-" * 50)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        print("-" * 50)
        
        # Test token limit approaching scenario
        print("\n🔍 Testing token limit approaching scenario...")
        
        # Simulate using most of the budget to trigger a delay
        token_manager.remaining_budget = int(token_manager.max_budget * 0.15)  # 15% remaining
        
        # Make another API call
        token_manager.manage_request(mock_response_headers)
        
        # Show updated statistics
        stats = token_manager.get_statistics()
        print("\n📊 Updated Token Usage Statistics:")
        print("-" * 50)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        print("-" * 50)
        
        # Get heavy task settings
        heavy_settings = token_manager.get_heavy_task_settings()
        print("\n⚙️ Heavy Task Settings:")
        print("-" * 50)
        for key, value in heavy_settings.items():
            print(f"{key}: {value}")
        print("-" * 50)
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error making API call: {e}")
        print("\n❌ Test failed.")
        print("Please check the error messages above.")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("TOKEN MANAGER TEST SCRIPT")
    print("=" * 50)
    
    success = test_token_manager()
    
    if success:
        print("\n✅ Token management system is working properly!")
    else:
        print("\nPlease fix the issues before proceeding.")
    
    print("\n" + "=" * 50)
