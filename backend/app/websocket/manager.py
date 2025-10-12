"""
WebSocket connection manager
Handles multiple WebSocket connections, user sessions, and connection lifecycle
"""

from fastapi import WebSocket
from typing import Dict, List, Optional, Set
import asyncio
import logging
import json
from datetime import datetime, timedelta

from app.config import settings
from app.models.responses import HeartbeatMessage, HeartbeatResponse, ErrorMessage

logger = logging.getLogger(__name__)

class ConnectionInfo:
    """Information about a WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, user_id: str, session_id: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.session_id = session_id
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.is_active = True

class WebSocketManager:
    """
    Manages WebSocket connections and handles connection lifecycle
    """
    
    def __init__(self):
        # Active connections: websocket -> ConnectionInfo
        self.active_connections: Dict[WebSocket, ConnectionInfo] = {}
        
        # User connections: user_id -> Set[WebSocket]
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        
        # Session connections: session_id -> WebSocket
        self.session_connections: Dict[str, WebSocket] = {}
        
        # Heartbeat task
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._start_heartbeat()

    async def connect(self, websocket: WebSocket, user_id: str, session_id: Optional[str] = None) -> bool:
        """
        Register a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            session_id: Optional session identifier
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Check connection limits per user
            user_connections = self.user_connections.get(user_id, set())
            if len(user_connections) >= settings.MAX_CONNECTIONS_PER_USER:
                logger.warning(f"User {user_id} exceeded connection limit")
                await websocket.send_json(
                    ErrorMessage(
                        error="Maximum connections exceeded",
                        code="CONNECTION_LIMIT"
                    ).dict()
                )
                return False
            
            # Create connection info
            conn_info = ConnectionInfo(websocket, user_id, session_id)
            
            # Register connection
            self.active_connections[websocket] = conn_info
            
            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            
            # Register session if provided
            if session_id:
                self.session_connections[session_id] = websocket
            
            logger.info(f"WebSocket connected: user={user_id}, session={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            return False

    async def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection
        
        Args:
            websocket: WebSocket connection to disconnect
        """
        try:
            if websocket not in self.active_connections:
                return
            
            conn_info = self.active_connections[websocket]
            user_id = conn_info.user_id
            session_id = conn_info.session_id
            
            # Remove from active connections
            del self.active_connections[websocket]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from session connections
            if session_id and session_id in self.session_connections:
                del self.session_connections[session_id]
            
            logger.info(f"WebSocket disconnected: user={user_id}, session={session_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")

    async def send_to_user(self, user_id: str, message: dict):
        """
        Send message to all connections of a specific user
        
        Args:
            user_id: User identifier
            message: Message to send
        """
        if user_id not in self.user_connections:
            return
        
        connections = self.user_connections[user_id].copy()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                await self.disconnect(websocket)

    async def send_to_session(self, session_id: str, message: dict):
        """
        Send message to a specific session
        
        Args:
            session_id: Session identifier
            message: Message to send
        """
        if session_id not in self.session_connections:
            return
        
        websocket = self.session_connections[session_id]
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to session {session_id}: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all active connections
        
        Args:
            message: Message to broadcast
        """
        connections = list(self.active_connections.keys())
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                await self.disconnect(websocket)

    def get_connection_info(self, websocket: WebSocket) -> Optional[ConnectionInfo]:
        """
        Get connection information for a WebSocket
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            ConnectionInfo or None if not found
        """
        return self.active_connections.get(websocket)

    def get_active_users(self) -> List[str]:
        """
        Get list of active user IDs
        
        Returns:
            List of user IDs with active connections
        """
        return list(self.user_connections.keys())

    def get_connection_count(self) -> int:
        """
        Get total number of active connections
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)

    def _start_heartbeat(self):
        """Start the heartbeat task"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        """
        Heartbeat loop to maintain connections and detect disconnects
        """
        while True:
            try:
                await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_INTERVAL)
                await self._send_heartbeat()
                await self._cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")

    async def _send_heartbeat(self):
        """Send heartbeat to all active connections"""
        if not self.active_connections:
            return
        
        heartbeat_msg = HeartbeatMessage().dict()
        connections = list(self.active_connections.keys())
        
        for websocket in connections:
            try:
                await websocket.send_json(heartbeat_msg)
            except Exception as e:
                logger.warning(f"Heartbeat failed for connection: {e}")
                await self.disconnect(websocket)

    async def _cleanup_stale_connections(self):
        """Clean up stale connections that haven't responded to heartbeat"""
        now = datetime.utcnow()
        stale_threshold = timedelta(seconds=settings.WEBSOCKET_HEARTBEAT_INTERVAL * 3)
        
        stale_connections = []
        for websocket, conn_info in self.active_connections.items():
            if now - conn_info.last_heartbeat > stale_threshold:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            logger.info("Cleaning up stale connection")
            await self.disconnect(websocket)

    async def update_heartbeat(self, websocket: WebSocket):
        """
        Update last heartbeat time for a connection
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections[websocket].last_heartbeat = datetime.utcnow()

    async def shutdown(self):
        """Shutdown the WebSocket manager"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        connections = list(self.active_connections.keys())
        for websocket in connections:
            try:
                await websocket.close()
            except:
                pass
        
        self.active_connections.clear()
        self.user_connections.clear()
        self.session_connections.clear()

