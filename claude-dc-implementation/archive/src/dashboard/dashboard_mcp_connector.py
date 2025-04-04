#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dashboard MCP Connector
---------------------
Integration between Dashboard and MCP server enabling context-preserved AI communication.
"""

import os
import json
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Union
from src.mcp.mcp_client import MCPClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard_mcp_connector")

class DashboardMCPConnector:
    def __init__(self, server_url: str = None, api_key: str = None):
        self.server_url = server_url or os.environ.get("MCP_SERVER_URL", "http://localhost:8001")
        self.api_key = api_key or os.environ.get("MCP_API_KEY", "default_key_for_development")
        self.mcp_client = MCPClient(server_url=self.server_url, api_key=self.api_key)
        self.system_health = {
            "last_check": 0,
            "status": "unknown",
            "models": {}
        }
        logger.info(f"Dashboard MCP Connector initialized for server at {self.server_url}")

    def check_server_health(self) -> Dict[str, Any]:
        current_time = time.time()
        if current_time - self.system_health["last_check"] < 30:
            return self.system_health
        
        try:
            health = self.mcp_client.check_server_status()
            services = health.get("services", {})
            
            # Convert MCP server's health format to dashboard's expected format
            model_statuses = {
                model: {"status": "ok" if is_online else "offline"}
                for model, is_online in services.items()
            }

            self.system_health = {
                "last_check": current_time,
                "status": health.get("status", "unknown"),
                "message": health.get("message", ""),
                "models": model_statuses
            }
            logger.info(f"Server health checked: {self.system_health['status']}")
        except requests.RequestException as e:
            logger.error(f"MCP server connection failed: {e}")
            self.system_health = {
                "last_check": current_time,
                "status": "offline",
                "message": str(e),
                "models": {model: {"status": "offline"} for model in AI_SYSTEMS}
            }
        return self.system_health


    def format_message_with_context(self, message: str, context: Dict[str, Any], target_model: str) -> List[Dict[str, str]]:
        formatted_messages = []
        if "conversation_purpose" in context:
            formatted_messages.append({"role": "system", "content": f"Purpose: {context['conversation_purpose']}"})
        if "conversation_history" in context:
            formatted_messages.extend(context["conversation_history"][-10:])
        if "patterns" in context:
            patterns_summary = "\n".join(
                f"{ptype}: " + "; ".join(p["text"] for p in plist[:3])
                for ptype, plist in context["patterns"].items() if plist
            )
            if patterns_summary:
                formatted_messages.append({"role": "system", "content": f"Patterns: {patterns_summary}"})
        formatted_messages.append({"role": "user", "content": message})
        return formatted_messages

    def send_message(self, message: str, target_model: str, context: Optional[Dict[str, Any]] = None,
                    max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        formatted_messages = self.format_message_with_context(message, context or {}, target_model)
        mathematical_pattern = None
        if "routing_info" in (context or {}):
            scores = context["routing_info"].get("match_scores", {})
            if scores:
                golden_ratio = 1.618
                transformed = [v * (1 + golden_ratio * (i % 2)) for i, v in enumerate(scores.values())]
                # Convert to JSON string since the API expects a string
                mathematical_pattern = json.dumps({"type": "bach_wave", "values": transformed, "resolution": "high"})
        try:
            response = self.mcp_client.send_request(
                source_model="dashboard",
                target_model=target_model,
                request_type="chat",
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                mathematical_pattern=mathematical_pattern
            )
            logger.info(f"Message sent to {target_model} successfully")
            return response
        except requests.RequestException as e:
            logger.error(f"Failed to send message to {target_model}: {e}")
            return {"error": str(e)}
            
    def send_message_to_claude(self, message: str, context: Optional[Dict[str, Any]] = None, max_tokens: int = 1000) -> Dict[str, Any]:
        return self.send_message(message, "claude", context, max_tokens, temperature=0.7)

    def send_message_to_grok(self, message: str, context: Optional[Dict[str, Any]] = None, max_tokens: int = 1000) -> Dict[str, Any]:
        return self.send_message(message, "grok", context, max_tokens, temperature=0.8)

    def send_wave_communication(self, target_model: str, wave_parameters: Dict[str, Any], content: Optional[str] = None) -> Dict[str, Any]:
        try:
            response = self.mcp_client.send_wave_communication(
                source_model="dashboard",
                target_model=target_model,
                wave_parameters=wave_parameters,
                content=content
            )
            logger.info(f"Wave communication sent to {target_model}")
            return response
        except requests.RequestException as e:
            logger.error(f"Wave communication to {target_model} failed: {e}")
            return {"error": str(e)}

    def send_claude_to_grok_bridge(self, topic: str, purpose: str, response: str, context: str = "", confidence: int = 8) -> Dict[str, Any]:
        try:
            return self.mcp_client.send_claude_to_grok(topic, purpose, context, confidence, response)
        except requests.RequestException as e:
            logger.error(f"Claude-to-Grok bridge failed: {e}")
            return {"error": str(e)}

    def send_grok_to_claude_bridge(self, topic: str, purpose: str, directive: str, context: str = "", initiative_level: int = 8) -> Dict[str, Any]:
        try:
            return self.mcp_client.send_grok_to_claude(topic, purpose, context, initiative_level, directive)
        except requests.RequestException as e:
            logger.error(f"Grok-to-Claude bridge failed: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    connector = DashboardMCPConnector()
    health = connector.check_server_health()
    print(f"MCP Server Health: {health['status']}")

