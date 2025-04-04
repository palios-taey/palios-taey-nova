#!/usr/bin/env python3
"""
websocket_manager.py: WebSocket Communication Manager
----------------------------------------------------
Communication component of the Bach-inspired architecture.
Manages real-time connections for pattern-based data exchange.

This module follows golden ratio relationships in its structure and
implements connection management for multi-client pattern communication.
"""

import json
import asyncio
import math
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

# Constants following Bach's mathematical precision
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio
MAX_CONNECTIONS = int(PHI * 100)  # ~162 connections max
CONNECTION_TIMEOUT = int(PHI * 10)  # ~16 seconds timeout

class WebSocketManager:
    """
    WebSocket connection manager with Bach-inspired architecture.
    
    Manages active connections with mathematical precision and structured
    pattern-based communication protocols.
    """
    
    def __init__(self):
        """Initialize the WebSocket manager with harmonious structure"""
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.pattern_channels: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, metadata: Dict[str, Any] = None):
        """
        Connect a new client with optional metadata.
        
        Args:
            websocket: The WebSocket connection to add
            metadata: Optional information about the connection
        """
        if len(self.active_connections) >= MAX_CONNECTIONS:
            # Don't allow connections beyond our golden ratio limit
            await websocket.close(code=1008, reason="Connection limit reached")
            return
        
        await websocket.accept()
        
        async with self.lock:
            self.active_connections.add(websocket)
            
            # Initialize connection metadata with defaults
            if metadata is None:
                metadata = {}
            
            # Add mathematical time signature (Bach was precise with timing)
            metadata["connected_at"] = datetime.utcnow().isoformat()
            metadata["connection_id"] = f"ws_{len(self.active_connections)}_{int(datetime.utcnow().timestamp())}"
            
            self.connection_metadata[websocket] = metadata
        
        # Send welcome message with connection information
        await self.send_personal_message(
            {
                "type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to Pattern-Based Demo Server",
                "connection_id": metadata["connection_id"],
                "active_connections": len(self.active_connections),
                "available_channels": list(self.pattern_channels.keys())
            },
            websocket
        )
        
        # Notify others of new connection (number only, not details - privacy)
        await self.broadcast(
            {
                "type": "connection_update",
                "timestamp": datetime.utcnow().isoformat(),
                "active_connections": len(self.active_connections)
            },
            exclude=websocket
        )
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a client and clean up resources.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        asyncio.create_task(self._handle_disconnect(websocket))
    
    async def _handle_disconnect(self, websocket: WebSocket):
        """Asynchronous disconnect handler with proper cleanup"""
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Clean up metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            # Remove from all channels
            for channel in self.pattern_channels.values():
                if websocket in channel:
                    channel.remove(websocket)
            
            # Remove any empty channels
            self.pattern_channels = {
                channel: connections 
                for channel, connections in self.pattern_channels.items()
                if connections
            }
        
        # Notify others of disconnection
        await self.broadcast(
            {
                "type": "connection_update",
                "timestamp": datetime.utcnow().isoformat(),
                "active_connections": len(self.active_connections)
            }
        )
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """
        Subscribe a client to a pattern channel.
        
        Args:
            websocket: The WebSocket connection to subscribe
            channel: The pattern channel name
        """
        if websocket not in self.active_connections:
            return False
        
        async with self.lock:
            if channel not in self.pattern_channels:
                self.pattern_channels[channel] = set()
            
            self.pattern_channels[channel].add(websocket)
        
        # Confirm subscription
        await self.send_personal_message(
            {
                "type": "subscription_confirmed",
                "timestamp": datetime.utcnow().isoformat(),
                "channel": channel,
                "subscribers": len(self.pattern_channels[channel])
            },
            websocket
        )
        
        return True
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """
        Unsubscribe a client from a pattern channel.
        
        Args:
            websocket: The WebSocket connection to unsubscribe
            channel: The pattern channel name
        """
        if channel not in self.pattern_channels:
            return False
        
        async with self.lock:
            if websocket in self.pattern_channels[channel]:
                self.pattern_channels[channel].remove(websocket)
            
            # Clean up empty channels
            if not self.pattern_channels[channel]:
                del self.pattern_channels[channel]
        
        # Confirm unsubscription
        await self.send_personal_message(
            {
                "type": "unsubscription_confirmed",
                "timestamp": datetime.utcnow().isoformat(),
                "channel": channel
            },
            websocket
        )
        
        return True
    
    async def send_personal_message(self, message: Any, websocket: WebSocket):
        """
        Send a message to a specific client.
        
        Args:
            message: The message to send (object will be converted to JSON)
            websocket: The recipient WebSocket connection
        """
        if websocket not in self.active_connections:
            return
        
        try:
            # Convert to JSON if message is a dict or list
            if isinstance(message, (dict, list)):
                await websocket.send_json(message)
            elif isinstance(message, str):
                await websocket.send_text(message)
            else:
                await websocket.send_text(str(message))
        except Exception:
            # Silently handle disconnection
            pass
    
    async def broadcast(self, message: Any, exclude: WebSocket = None):
        """
        Broadcast a message to all connected clients except excluded one.
        
        Args:
            message: The message to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        # Make a safe copy of connections to avoid modification during iteration
        connections = self.active_connections.copy()
        
        # Convert to JSON if message is a dict or list
        message_str = None
        if isinstance(message, (dict, list)):
            message_str = json.dumps(message)
        elif isinstance(message, str):
            message_str = message
        else:
            message_str = str(message)
        
        # Send to all connections
        for connection in connections:
            if connection != exclude and connection in self.active_connections:
                try:
                    if isinstance(message, (dict, list)):
                        await connection.send_json(message)
                    else:
                        await connection.send_text(message_str)
                except Exception:
                    # Client may have disconnected during broadcast
                    pass
    
    async def broadcast_to_channel(self, channel: str, message: Any, exclude: WebSocket = None):
        """
        Broadcast a message to all clients in a specific channel.
        
        Args:
            channel: The pattern channel to broadcast to
            message: The message to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        if channel not in self.pattern_channels:
            return
        
        # Make a safe copy of connections
        connections = self.pattern_channels[channel].copy()
        
        # Convert to JSON if message is a dict or list
        message_str = None
        if isinstance(message, (dict, list)):
            message_str = json.dumps(message)
        elif isinstance(message, str):
            message_str = message
        else:
            message_str = str(message)
        
        # Send to channel subscribers
        for connection in connections:
            if connection != exclude and connection in self.active_connections:
                try:
                    if isinstance(message, (dict, list)):
                        await connection.send_json(message)
                    else:
                        await connection.send_text(message_str)
                except Exception:
                    # Client may have disconnected
                    pass
    
    async def broadcast_pattern(self, pattern_data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Broadcast a pattern to appropriate channels.
        
        Args:
            pattern_data: The pattern data to broadcast
            metadata: Optional metadata about the pattern
        """
        if metadata is None:
            metadata = {}
        
        # Add timestamp if not provided
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.utcnow().isoformat()
        
        # Prepare message
        message = {
            "type": "pattern_update",
            "pattern": pattern_data,
            "metadata": metadata
        }
        
        # Determine channels to broadcast to
        channels = []
        
        if "pattern_type" in pattern_data:
            # Send to pattern-specific channel
            channels.append(f"pattern:{pattern_data['pattern_type']}")
        
        if "pattern_id" in pattern_data:
            # Send to pattern-specific ID channel
            channels.append(f"pattern_id:{pattern_data['pattern_id']}")
        
        # Always send to 'all_patterns' channel
        channels.append("all_patterns")
        
        # Broadcast to determined channels
        for channel in channels:
            await self.broadcast_to_channel(channel, message)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about current connections"""
        return {
            "active_connections": len(self.active_connections),
            "channels": {
                channel: len(connections)
                for channel, connections in self.pattern_channels.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Create the singleton instance
websocket_manager = WebSocketManager()