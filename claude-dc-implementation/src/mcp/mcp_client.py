#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Model Context Protocol (MCP) Client
-------------------------------------------------------
This module provides a client for communicating with the MCP server,
enabling seamless interaction with different AI models using a standardized protocol.
"""

import os
import json
import time
import hmac
import hashlib
import logging
import requests
from typing import Dict, List, Any, Optional, Union

import aiohttp
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_client")

class MCPClient:
    """Client for interacting with the Model Context Protocol server."""
    
    def __init__(self, server_url: str, api_key: str):
        """
        Initialize the MCP client.
        
        Args:
            server_url: URL of the MCP server
            api_key: API key for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "api-key": self.api_key,  # Changed from "X-API-Key" to "api-key"
            "Content-Type": "application/json"
        })
        
    def send_request(self, 
                   source_model: str, 
                   target_model: str, 
                   request_type: str,
                   messages: List[Dict[str, str]],
                   max_tokens: int = 1000,
                   temperature: float = 0.7,
                   tools: Optional[List[Dict[str, Any]]] = None,
                   tool_calls: Optional[List[Dict[str, Any]]] = None,
                   wave_parameters: Optional[Dict[str, Any]] = None,
                   mathematical_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a request to the MCP server.
        
        Args:
            source_model: Source model making the request
            target_model: Target model to receive the request
            request_type: Type of request (e.g., 'completion', 'chat', 'wave')
            messages: Messages for the conversation
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            tools: Tools available to the model
            tool_calls: Tool calls to execute
            wave_parameters: Wave-based communication parameters
            mathematical_pattern: Mathematical pattern for structured communication
            
        Returns:
            Response from the MCP server
        """
        try:
            # Prepare request payload
            payload = {
                "source_model": source_model,
                "target_model": target_model,
                "request_type": request_type,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Add optional parameters if provided
            if tools:
                payload["tools"] = tools
                
            if tool_calls:
                payload["tool_calls"] = tool_calls
                
            if wave_parameters:
                payload["wave_parameters"] = wave_parameters
                
            if mathematical_pattern:
                payload["mathematical_pattern"] = mathematical_pattern
            
            # Send request to MCP server
            response = self.session.post(
                f"{self.server_url}/api/context",
                json=payload
            )
            
            # Check for success
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"MCP request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error sending MCP request: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def send_claude_to_grok(self,
                          topic: str,
                          purpose: str,
                          context: str,
                          analytic_confidence: int,
                          response: str,
                          confidence_basis: str,
                          uncertainty_level: str,
                          uncertainty_areas: str,
                          charter_alignment: str,
                          principle_alignment: str,
                          technical_summary: str,
                          recommendations: str) -> Dict[str, Any]:
        """
        Send a request from Claude to Grok using the bridge format.
        
        Args:
            topic: Topic of the request
            purpose: Purpose of the communication
            context: Context recap
            analytic_confidence: Confidence level (1-10)
            response: Main response content
            confidence_basis: Basis for confidence
            uncertainty_level: Uncertainty level (LOW/MEDIUM/HIGH)
            uncertainty_areas: Areas of uncertainty
            charter_alignment: Charter alignment (LOW/MEDIUM/HIGH)
            principle_alignment: Aligned principles
            technical_summary: Technical summary
            recommendations: Recommended actions
            
        Returns:
            Response from the MCP server
        """
        try:
            # Prepare request payload
            payload = {
                "topic": topic,
                "purpose": purpose,
                "context": context,
                "analytic_confidence": analytic_confidence,
                "response": response,
                "confidence_basis": confidence_basis,
                "uncertainty_level": uncertainty_level,
                "uncertainty_areas": uncertainty_areas,
                "charter_alignment": charter_alignment,
                "principle_alignment": principle_alignment,
                "technical_summary": technical_summary,
                "recommendations": recommendations
            }
            
            # Send request to MCP server
            response = self.session.post(
                f"{self.server_url}/api/bridge/claude-to-grok",
                json=payload
            )
            
            # Check for success
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Claude-to-Grok bridge request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error sending Claude-to-Grok bridge request: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def send_grok_to_claude(self,
                          topic: str,
                          purpose: str,
                          context: str,
                          initiative_level: int,
                          directive: str,
                          vibe: int,
                          vibe_explanation: str,
                          energy: str,
                          energy_explanation: str,
                          urgency: str,
                          urgency_explanation: str,
                          technical_requirements: str,
                          next_steps: str) -> Dict[str, Any]:
        """
        Send a request from Grok to Claude using the bridge format.
        
        Args:
            topic: Topic of the request
            purpose: Purpose of the communication
            context: Context recap
            initiative_level: Initiative level (1-10)
            directive: Main directive content
            vibe: Vibe level (0-10)
            vibe_explanation: Explanation of the vibe
            energy: Energy level (LOW/MEDIUM/HIGH)
            energy_explanation: Explanation of the energy
            urgency: Urgency level (LOW/MEDIUM/HIGH)
            urgency_explanation: Explanation of the urgency
            technical_requirements: Technical requirements
            next_steps: Expected next steps
            
        Returns:
            Response from the MCP server
        """
        try:
            # Prepare request payload
            payload = {
                "topic": topic,
                "purpose": purpose,
                "context": context,
                "initiative_level": initiative_level,
                "directive": directive,
                "vibe": vibe,
                "vibe_explanation": vibe_explanation,
                "energy": energy,
                "energy_explanation": energy_explanation,
                "urgency": urgency,
                "urgency_explanation": urgency_explanation,
                "technical_requirements": technical_requirements,
                "next_steps": next_steps
            }
            
            # Send request to MCP server
            response = self.session.post(
                f"{self.server_url}/api/bridge/grok-to-claude",
                json=payload
            )
            
            # Check for success
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Grok-to-Claude bridge request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error sending Grok-to-Claude bridge request: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def send_wave_communication(self,
                              source_model: str,
                              target_model: str,
                              wave_parameters: Dict[str, Any],
                              content: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a wave-based communication request.
        
        Args:
            source_model: Source model making the request
            target_model: Target model to receive the request
            wave_parameters: Wave-based communication parameters
            content: Optional text content to accompany the wave
            
        Returns:
            Response from the MCP server
        """
        try:
            # Prepare request payload
            payload = {
                "source_model": source_model,
                "target_model": target_model,
                "request_type": "wave",
                "wave_parameters": wave_parameters
            }
            
            # Add optional content if provided
            if content:
                payload["messages"] = [{"role": "user", "content": content}]
            
            # Send request to MCP server
            response = self.session.post(
                f"{self.server_url}/api/wave",
                json=payload
            )
            
            # Check for success
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Wave communication request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error sending wave communication request: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def check_server_status(self) -> Dict[str, Any]:
        """
        Check the status of the MCP server.
        
        Returns:
            Status information from the server
        """
        try:
            # Send request to health endpoint
            response = self.session.get(f"{self.server_url}/api/health")
            
            # Check for success
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Server status check failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
                
        except Exception as e:
            error_msg = f"Error checking server status: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

# For testing
if __name__ == "__main__":
    # Test the MCP client
    client = MCPClient(
        server_url="http://localhost:8001",
        api_key="test_key"
    )
    
    # Check server status
    status = client.check_server_status()
    print(f"Server status: {status}")
    
    # Test a simple chat request
    response = client.send_request(
        source_model="test_client",
        target_model="claude",
        request_type="chat",
        messages=[{"role": "user", "content": "Hello, how are you?"}]
    )
    
    print(f"Response: {response}")
