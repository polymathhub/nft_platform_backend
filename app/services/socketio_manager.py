"""
Socket.io Real-time Notifications Manager
Handles WebSocket connections and broadcasts notifications to clients
"""

import logging
from typing import Dict, Set, Optional
from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI
import json

logger = logging.getLogger(__name__)

class SocketioManager:
    """Manages Socket.io connections and real-time notifications"""
    
    def __init__(self):
        self.sio: Optional[AsyncServer] = None
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of socket_ids
        self.socket_to_user: Dict[str, str] = {}  # socket_id -> user_id
        
    def initialize(self, app: FastAPI):
        """Initialize Socket.io server and attach to FastAPI app"""
        try:
            # Create AsyncServer
            self.sio = AsyncServer(
                async_mode='asgi',
                cors_allowed_origins='*',
                ping_timeout=10,
                ping_interval=5,
                logger=False,  # disable built-in logging
                engineio_logger=False,
            )
            
            # Setup event handlers
            self._setup_handlers()
            
            # Wrap FastAPI app with Socket.io ASGI app
            socketio_app = ASGIApp(self.sio, app)
            app.mount('/socket.io', socketio_app, name='socketio')
            
            logger.info("✅ Socket.io initialized and mounted")
            return socketio_app
        except Exception as e:
            logger.error(f"❌ Failed to initialize Socket.io: {e}", exc_info=True)
            return None
    
    def _setup_handlers(self):
        """Register Socket.io event handlers"""
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"Client connected: {sid}")
            # Extract user_id from query params if available
            query_string = environ.get('QUERY_STRING', '')
            # In production, validate auth token from query params
            
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            # Remove user connection mapping
            if sid in self.socket_to_user:
                user_id = self.socket_to_user[sid]
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(sid)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                del self.socket_to_user[sid]
                logger.info(f"Client disconnected: {sid} (user: {user_id})")
            else:
                logger.info(f"Client disconnected: {sid}")
        
        @self.sio.event
        async def register_user(sid, data):
            """Register socket with a user_id for targeted notifications"""
            try:
                user_id = data.get('user_id')
                if not user_id:
                    logger.warning(f"Register user received without user_id: {sid}")
                    return
                
                # Map socket to user
                self.socket_to_user[sid] = user_id
                
                # Add socket to user's connection set
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(sid)
                
                logger.info(f"✅ User {user_id} registered with socket {sid}")
                await self.sio.emit('registration_confirmed', {'user_id': user_id}, to=sid)
            except Exception as e:
                logger.error(f"Error registering user: {e}")
    
    async def broadcast_notification(self, user_id: str, event: str, data: dict):
        """Send notification to all sockets of a specific user"""
        if not self.sio:
            logger.warning("Socket.io server not initialized")
            return
        
        if user_id not in self.user_connections:
            logger.debug(f"User {user_id} has no active connections")
            return
        
        try:
            for socket_id in self.user_connections[user_id]:
                await self.sio.emit(event, data, to=socket_id)
            logger.debug(f"Broadcasted {event} to {len(self.user_connections[user_id])} sockets of user {user_id}")
        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")
    
    async def notify_all(self, event: str, data: dict):
        """Broadcast to all connected clients"""
        if not self.sio:
            return
        
        try:
            await self.sio.emit(event, data)
            logger.debug(f"Broadcasted {event} to all clients")
        except Exception as e:
            logger.error(f"Error broadcasting to all: {e}")
    
    async def send_nft_minted(self, user_id: str, nft_data: dict):
        """Send NFT minted notification"""
        await self.broadcast_notification(user_id, 'nft:minted', {
            'title': 'NFT Minted',
            'message': f"Your NFT '{nft_data.get('name', 'NFT')}' has been successfully minted!",
            'nft_id': str(nft_data.get('id', '')),
            'timestamp': nft_data.get('created_at'),
        })
    
    async def send_wallet_connected(self, user_id: str, wallet_data: dict):
        """Send wallet connected notification"""
        await self.broadcast_notification(user_id, 'wallet:connected', {
            'title': 'Wallet Connected',
            'message': f"Wallet {wallet_data.get('address', '')[:6]}... connected successfully",
            'blockchain': wallet_data.get('blockchain'),
            'timestamp': wallet_data.get('created_at'),
        })
    
    async def send_transaction_confirmed(self, user_id: str, tx_data: dict):
        """Send transaction confirmed notification"""
        await self.broadcast_notification(user_id, 'transaction:confirmed', {
            'title': 'Transaction Confirmed',
            'message': f"Your transaction has been confirmed",
            'transaction_hash': tx_data.get('hash'),
            'status': tx_data.get('status'),
            'timestamp': tx_data.get('timestamp'),
        })


# Global instance
socketio_manager = SocketioManager()
