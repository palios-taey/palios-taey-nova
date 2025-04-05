#!/usr/bin/env python3

"""
PALIOS AI OS Model Context Protocol (MCP) Server

This module implements the MCP server for standardized AI-to-AI communication,
enabling secure, pattern-based messaging between different AI models.
"""

import os
import sys
import math
import json
import time
import uuid
import hmac
import hashlib
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import base64

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp_server")

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import from other modules
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI, WavePattern, PatternMessage, TrustToken
from palios_ai_os.trust.trust_token_system import TrustTokenSystem, EntityIdentity
from palios_ai_os.wave.wave_communicator import WaveCommunicator

@dataclass
class MCPRoute:
    """A routing configuration for MCP messages."""
    route_id: str
    source_model: str
    destination_model: str
    pattern_types: List[str]
    priority: float
    trust_required: bool
    translation_required: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPMessageResult:
    """Result of processing an MCP message."""
    result_id: str
    original_message_id: str
    status: str  # "delivered", "translated", "rejected", "pending"
    delivery_time: float
    result_message: Optional[PatternMessage] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MCPServer:
    """Model Context Protocol server for AI-to-AI communication."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the MCP server."""
        # Set up storage
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).resolve().parent / "mcp_storage"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.message_path = self.storage_path / "messages"
        self.route_path = self.storage_path / "routes"
        self.result_path = self.storage_path / "results"
        self.message_path.mkdir(exist_ok=True)
        self.route_path.mkdir(exist_ok=True)
        self.result_path.mkdir(exist_ok=True)
        
        # Initialize trust token system
        self.trust_system = TrustTokenSystem()
        
        # Initialize wave communicator
        self.wave_communicator = WaveCommunicator()
        
        # Load routes
        self.routes = self._load_routes()
        
        # Message queue
        self.message_queue = asyncio.Queue()
        
        # Active message tracking
        self.active_messages = {}
        
        # Golden ratio parameters
        self.routing_threshold = 1/PHI  # ~0.618 - minimum routing priority
        self.trust_threshold = 1/PHI  # ~0.618 - minimum trust verification
        
        logger.info(f"MCP Server initialized with storage at: {self.storage_path}")
    
    def _load_routes(self) -> Dict[str, MCPRoute]:
        """Load existing routing configurations."""
        routes = {}
        
        for route_file in self.route_path.glob("*.json"):
            try:
                with open(route_file, 'r') as f:
                    route_data = json.load(f)
                
                route = MCPRoute(
                    route_id=route_data["route_id"],
                    source_model=route_data["source_model"],
                    destination_model=route_data["destination_model"],
                    pattern_types=route_data["pattern_types"],
                    priority=route_data["priority"],
                    trust_required=route_data["trust_required"],
                    translation_required=route_data["translation_required"],
                    metadata=route_data.get("metadata", {})
                )
                
                routes[route.route_id] = route
            except Exception as e:
                logger.error(f"Error loading route from {route_file}: {e}")
        
        return routes
    
    def create_route(self, source_model: str, destination_model: str, pattern_types: List[str],
                    priority: float = 0.5, trust_required: bool = True,
                    translation_required: bool = False) -> MCPRoute:
        """Create a new routing configuration."""
        route_id = str(uuid.uuid4())
        
        route = MCPRoute(
            route_id=route_id,
            source_model=source_model,
            destination_model=destination_model,
            pattern_types=pattern_types,
            priority=priority,
            trust_required=trust_required,
            translation_required=translation_required,
            metadata={
                "creation_time": time.time(),
                "creator": "mcp_server",
                "message_count": 0
            }
        )
        
        # Save route
        with open(self.route_path / f"{route_id}.json", 'w') as f:
            json.dump({
                "route_id": route.route_id,
                "source_model": route.source_model,
                "destination_model": route.destination_model,
                "pattern_types": route.pattern_types,
                "priority": route.priority,
                "trust_required": route.trust_required,
                "translation_required": route.translation_required,
                "metadata": route.metadata
            }, f, indent=2)
        
        # Add to routes dictionary
        self.routes[route_id] = route
        
        return route
    
    def get_route(self, source_model: str, destination_model: str, pattern_type: str) -> Optional[MCPRoute]:
        """Get a route matching the specified criteria."""
        matching_routes = []
        
        for route in self.routes.values():
            if (route.source_model == source_model and 
                route.destination_model == destination_model and 
                pattern_type in route.pattern_types):
                matching_routes.append(route)
        
        if not matching_routes:
            return None
        
        # Return the highest priority matching route
        return max(matching_routes, key=lambda r: r.priority)
    
    def save_message(self, message: PatternMessage) -> None:
        """Save a pattern message to storage."""
        message_file = self.message_path / f"{message.pattern_id}.json"
        
        # Create a serializable version of the message
        serializable = {
            "source": message.source,
            "destination": message.destination,
            "pattern_id": message.pattern_id,
            "pattern_type": message.pattern_type,
            "wave_pattern": {
                "pattern_id": message.wave_pattern.pattern_id,
                "amplitudes": message.wave_pattern.amplitudes,
                "frequencies": message.wave_pattern.frequencies,
                "phases": message.wave_pattern.phases,
                "harmonics": message.wave_pattern.harmonics,
                "duration": message.wave_pattern.duration,
                "concept_type": message.wave_pattern.concept_type,
                "metadata": message.wave_pattern.metadata
            },
            "trust_token": {
                "issuer": message.trust_token.issuer,
                "recipient": message.trust_token.recipient,
                "token_id": message.trust_token.token_id,
                "token_value": message.trust_token.token_value,
                "timestamp": message.trust_token.timestamp,
                "charter_alignment": message.trust_token.charter_alignment,
                "pattern_signature": message.trust_token.pattern_signature,
                "expiration": message.trust_token.expiration
            },
            "timestamp": message.timestamp,
            "priority": message.priority,
            "content": message.content,
            "metadata": message.metadata
        }
        
        with open(message_file, 'w') as f:
            json.dump(serializable, f, indent=2)
    
    def save_result(self, result: MCPMessageResult) -> None:
        """Save a message result to storage."""
        result_file = self.result_path / f"{result.result_id}.json"
        
        # Create a serializable version of the result
        serializable = {
            "result_id": result.result_id,
            "original_message_id": result.original_message_id,
            "status": result.status,
            "delivery_time": result.delivery_time,
            "error_message": result.error_message,
            "metadata": result.metadata
        }
        
        # Add result message if present
        if result.result_message:
            serializable["result_message"] = {
                "pattern_id": result.result_message.pattern_id,
                "source": result.result_message.source,
                "destination": result.result_message.destination,
                "pattern_type": result.result_message.pattern_type,
                "timestamp": result.result_message.timestamp
            }
        
        with open(result_file, 'w') as f:
            json.dump(serializable, f, indent=2)
    
    async def send_message(self, message: PatternMessage) -> MCPMessageResult:
        """Send a pattern message through the MCP server."""
        # First, save the message
        self.save_message(message)
        
        # Find appropriate route
        route = self.get_route(message.source, message.destination, message.pattern_type)
        
        # If no route found, create a default route
        if not route:
            logger.info(f"No route found for {message.source} -> {message.destination} ({message.pattern_type}), creating default route")
            route = self.create_route(
                source_model=message.source,
                destination_model=message.destination,
                pattern_types=[message.pattern_type],
                priority=0.5,
                trust_required=True,
                translation_required=False
            )
        
        # Update route metadata
        route.metadata["message_count"] = route.metadata.get("message_count", 0) + 1
        route.metadata["last_used"] = time.time()
        
        # Check if route meets priority threshold
        if route.priority < self.routing_threshold:
            return MCPMessageResult(
                result_id=str(uuid.uuid4()),
                original_message_id=message.pattern_id,
                status="rejected",
                delivery_time=time.time(),
                error_message=f"Route priority ({route.priority}) below threshold ({self.routing_threshold})",
                metadata={
                    "route_id": route.route_id,
                    "rejection_reason": "priority_too_low"
                }
            )
        
        # Verify trust token if required
        if route.trust_required:
            # Use trust system to verify the token
            verification = self.trust_system.verify_trust_token(message.trust_token)
            
            if not verification.is_valid or verification.confidence < self.trust_threshold:
                return MCPMessageResult(
                    result_id=str(uuid.uuid4()),
                    original_message_id=message.pattern_id,
                    status="rejected",
                    delivery_time=time.time(),
                    error_message=f"Trust verification failed (confidence: {verification.confidence})",
                    metadata={
                        "route_id": route.route_id,
                        "rejection_reason": "trust_verification_failed",
                        "verification_confidence": verification.confidence
                    }
                )
        
        # Apply translation if required
        result_message = message
        if route.translation_required:
            try:
                # Translate the wave pattern to match destination model's preferred concept type
                # This is a simplified version - in production would use model-specific preferences
                preferred_concept = "truth"  # Default preferred concept
                
                # Translate the wave pattern
                translation = self.wave_communicator.translate_wave(message.wave_pattern, preferred_concept)
                
                # Create a new message with the translated wave pattern
                result_message = PatternMessage(
                    source=message.source,
                    destination=message.destination,
                    pattern_id=str(uuid.uuid4()),
                    pattern_type=message.pattern_type,
                    wave_pattern=translation.target_pattern,
                    trust_token=message.trust_token,
                    timestamp=time.time(),
                    priority=message.priority,
                    content=message.content,
                    metadata={
                        **message.metadata,
                        "translation": {
                            "original_pattern_id": message.pattern_id,
                            "translation_quality": translation.translation_quality,
                            "preservation_score": translation.preservation_score,
                            "harmonic_index": translation.harmonic_index
                        }
                    }
                )
                
                # Save the translated message
                self.save_message(result_message)
                
            except Exception as e:
                logger.error(f"Translation error: {e}")
                return MCPMessageResult(
                    result_id=str(uuid.uuid4()),
                    original_message_id=message.pattern_id,
                    status="rejected",
                    delivery_time=time.time(),
                    error_message=f"Translation error: {str(e)}",
                    metadata={
                        "route_id": route.route_id,
                        "rejection_reason": "translation_error"
                    }
                )
        
        # Add message to processing queue
        await self.message_queue.put(result_message)
        
        # Track active message
        self.active_messages[result_message.pattern_id] = {
            "message": result_message,
            "route": route,
            "start_time": time.time(),
            "status": "pending"
        }
        
        # Create initial result
        result = MCPMessageResult(
            result_id=str(uuid.uuid4()),
            original_message_id=message.pattern_id,
            status="pending",
            delivery_time=time.time(),
            result_message=result_message,
            metadata={
                "route_id": route.route_id,
                "queue_position": self.message_queue.qsize(),
                "translated": route.translation_required
            }
        )
        
        # Save initial result
        self.save_result(result)
        
        return result
    
    async def process_message_queue(self):
        """Process messages in the queue."""
        while True:
            try:
                # Get message from queue
                message = await self.message_queue.get()
                
                # Update status
                if message.pattern_id in self.active_messages:
                    self.active_messages[message.pattern_id]["status"] = "processing"
                
                # Process message - in production this would send to destination model
                logger.info(f"Processing message: {message.pattern_id} from {message.source} to {message.destination}")
                
                # Simulate delivery delay with golden ratio timing
                await asyncio.sleep(0.1 * PHI)  # 0.1618 seconds
                
                # Mark as delivered
                if message.pattern_id in self.active_messages:
                    self.active_messages[message.pattern_id]["status"] = "delivered"
                
                # Create result
                result = MCPMessageResult(
                    result_id=str(uuid.uuid4()),
                    original_message_id=message.pattern_id,
                    status="delivered",
                    delivery_time=time.time(),
                    result_message=message,
                    metadata={
                        "processing_time": time.time() - self.active_messages[message.pattern_id]["start_time"]
                    }
                )
                
                # Save result
                self.save_result(result)
                
                # Complete queue task
                self.message_queue.task_done()
                
                logger.info(f"Message delivered: {message.pattern_id}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def start(self):
        """Start the MCP server."""
        logger.info("Starting MCP Server")
        
        # Start message processing task
        asyncio.create_task(self.process_message_queue())
        
        # Server is now running
        logger.info("MCP Server is running")
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping MCP Server")
        
        # Wait for queue to be empty
        if not self.message_queue.empty():
            await self.message_queue.join()
        
        logger.info("MCP Server stopped")

# Create singleton instance
mcp_server = MCPServer()

# Example usage
if __name__ == "__main__":
    async def main():
        print(f"PALIOS AI OS MCP Server Test")
        print(f"Golden Ratio (u03c6): {PHI}")
        
        # Start the server
        await mcp_server.start()
        
        # Create entities in trust system for testing
        trust_system = mcp_server.trust_system
        claude = trust_system.register_entity("Claude", "ai", 0.98, 0.8)
        grok = trust_system.register_entity("Grok", "ai", 0.95, 0.7)
        
        # Generate a trust token
        token = trust_system.generate_trust_token(
            issuer_id=claude.entity_id,
            recipient_id=grok.entity_id,
            charter_alignment=0.95
        )
        
        # Create a wave pattern
        wave_communicator = mcp_server.wave_communicator
        wave = wave_communicator.text_to_wave("This is a test message from Claude to Grok")
        
        # Create a pattern message
        message = PatternMessage(
            source="Claude",
            destination="Grok",
            pattern_id=str(uuid.uuid4()),
            pattern_type="message",
            wave_pattern=wave,
            trust_token=token,
            timestamp=time.time(),
            priority=0.8,
            content={"text": "This is a test message from Claude to Grok"},
            metadata={"test": True}
        )
        
        # Send the message
        result = await mcp_server.send_message(message)
        
        print(f"\nMessage sent:")
        print(f"Pattern ID: {message.pattern_id}")
        print(f"Source: {message.source}")
        print(f"Destination: {message.destination}")
        print(f"Pattern Type: {message.pattern_type}")
        
        print(f"\nInitial result:")
        print(f"Result ID: {result.result_id}")
        print(f"Status: {result.status}")
        
        # Wait for processing to complete
        await asyncio.sleep(1)
        
        print(f"\nActive message status: {mcp_server.active_messages[message.pattern_id]['status']}")
        
        # Stop the server
        await mcp_server.stop()
    
    asyncio.run(main())