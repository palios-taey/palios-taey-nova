#!/usr/bin/env python
"""
PALIOS-TAEY Integration Test

This script tests the deployed PALIOS-TAEY application by sending requests
to each of the key endpoints.
"""

import argparse
import json
import logging
import requests
import sys
import time
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class PaliosTaeyClient:
    """Client for testing PALIOS-TAEY deployment"""
    
    def __init__(self, base_url: str):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the PALIOS-TAEY deployment
        """
        self.base_url = base_url
        logger.info(f"Initialized client for {base_url}")
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health endpoint
        
        Returns:
            Health check response
        """
        url = f"{self.base_url}/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_root(self) -> Dict[str, Any]:
        """
        Get the root endpoint
        
        Returns:
            Root endpoint response
        """
        response = requests.get(self.base_url)
        response.raise_for_status()
        return response.json()
    
    def test_memory(self) -> Dict[str, Any]:
        """
        Test the memory endpoint
        
        Returns:
            Memory endpoint response
        """
        url = f"{self.base_url}/api/memory"
        response = requests.post(url, json={
            "content": {"test": "data"},
            "tags": ["test"]
        })
        response.raise_for_status()
        return response.json()
    
    def test_models(self) -> Dict[str, Any]:
        """
        Test the models endpoint
        
        Returns:
            Models endpoint response
        """
        url = f"{self.base_url}/api/models"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def test_tasks(self) -> Dict[str, Any]:
        """
        Test the tasks endpoint
        
        Returns:
            Tasks endpoint response
        """
        url = f"{self.base_url}/api/tasks"
        response = requests.post(url, json={
            "task_type": "test_task",
            "content": {"test": "data"}
        })
        response.raise_for_status()
        return response.json()
    
    def test_routing(self) -> Dict[str, Any]:
        """
        Test the routing endpoint
        
        Returns:
            Routing endpoint response
        """
        url = f"{self.base_url}/api/route"
        response = requests.post(url, json={
            "task_type": "test_task",
            "content": {"test": "data"}
        })
        response.raise_for_status()
        return response.json()
    
    def test_transcripts(self) -> Dict[str, Any]:
        """
        Test the transcripts endpoint
        
        Returns:
            Transcripts endpoint response
        """
        url = f"{self.base_url}/api/transcripts"
        response = requests.post(url, json={
            "format_type": "raw",
            "transcript_data": "Test transcript data"
        })
        response.raise_for_status()
        return response.json()
    
    def test_protocols(self) -> Dict[str, Any]:
        """
        Test the protocols endpoint
        
        Returns:
            Protocols endpoint response
        """
        url = f"{self.base_url}/api/protocols"
        response = requests.post(url, json={
            "name": "test_protocol",
            "version": "1.0",
            "description": "Test protocol",
            "structure": {}
        })
        response.raise_for_status()
        return response.json()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all tests
        
        Returns:
            Test results
        """
        results = {}
        
        try:
            logger.info("Testing health endpoint...")
            results["health"] = self.check_health()
            logger.info("Health check passed")
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            results["health"] = {"error": str(e)}
        
        try:
            logger.info("Testing root endpoint...")
            results["root"] = self.get_root()
            logger.info("Root endpoint test passed")
        except Exception as e:
            logger.error(f"Root endpoint test failed: {str(e)}")
            results["root"] = {"error": str(e)}
        
        try:
            logger.info("Testing memory endpoint...")
            results["memory"] = self.test_memory()
            logger.info("Memory endpoint test passed")
        except Exception as e:
            logger.error(f"Memory endpoint test failed: {str(e)}")
            results["memory"] = {"error": str(e)}
        
        try:
            logger.info("Testing models endpoint...")
            results["models"] = self.test_models()
            logger.info("Models endpoint test passed")
        except Exception as e:
            logger.error(f"Models endpoint test failed: {str(e)}")
            results["models"] = {"error": str(e)}
        
        try:
            logger.info("Testing tasks endpoint...")
            results["tasks"] = self.test_tasks()
            logger.info("Tasks endpoint test passed")
        except Exception as e:
            logger.error(f"Tasks endpoint test failed: {str(e)}")
            results["tasks"] = {"error": str(e)}
        
        try:
            logger.info("Testing routing endpoint...")
            results["routing"] = self.test_routing()
            logger.info("Routing endpoint test passed")
        except Exception as e:
            logger.error(f"Routing endpoint test failed: {str(e)}")
            results["routing"] = {"error": str(e)}
        
        try:
            logger.info("Testing transcripts endpoint...")
            results["transcripts"] = self.test_transcripts()
            logger.info("Transcripts endpoint test passed")
        except Exception as e:
            logger.error(f"Transcripts endpoint test failed: {str(e)}")
            results["transcripts"] = {"error": str(e)}
        
        try:
            logger.info("Testing protocols endpoint...")
            results["protocols"] = self.test_protocols()
            logger.info("Protocols endpoint test passed")
        except Exception as e:
            logger.error(f"Protocols endpoint test failed: {str(e)}")
            results["protocols"] = {"error": str(e)}
        
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PALIOS-TAEY Integration Test")
    parser.add_argument("--base-url", default="https://palios-taey-abcd-uc.a.run.app", help="Base URL of the PALIOS-TAEY deployment")
    args = parser.parse_args()
    
    client = PaliosTaeyClient(args.base_url)
    
    try:
        results = client.run_all_tests()
        
        # Print results
        print(json.dumps(results, indent=2))
        
        # Check if any tests failed
        failed_tests = [test for test, result in results.items() if "error" in result]
        
        if failed_tests:
            logger.error(f"Failed tests: {', '.join(failed_tests)}")
            return 1
        
        logger.info("All tests passed!")
        return 0
    except Exception as e:
        logger.error(f"Test run failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
