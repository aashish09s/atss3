from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from typing import Dict, List, Optional
import json
import asyncio
from app.utils.tokens import decode_token
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

# Suppress noisy WebSocket close logs - these are normal during reconnections
import logging
websocket_logger = logging.getLogger("websockets")
websocket_logger.setLevel(logging.WARNING)

router = APIRouter(tags=["WebSocket"])

# Simple in-memory connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        """Send message to user with proper error handling for closed connections"""
        if user_id not in self.active_connections:
            return
        
        dead_connections = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message)
            except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK, RuntimeError) as e:
                # Connection is closed - mark for removal
                print(f"[WEBSOCKET] Connection closed for user {user_id}: {type(e).__name__}")
                dead_connections.append(connection)
            except Exception as e:
                # Other errors - log and mark for removal
                print(f"[WEBSOCKET] Error sending message to user {user_id}: {type(e).__name__}: {e}")
                dead_connections.append(connection)
        
        # Remove dead connections
        for dead_conn in dead_connections:
            if dead_conn in self.active_connections[user_id]:
                self.active_connections[user_id].remove(dead_conn)
        
        # Clean up empty user connections
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def broadcast_to_users(self, message: str, user_ids: List[str]):
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

manager = ConnectionManager()


@router.websocket("/ws/resume-sync")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None), user_id: Optional[str] = Query(None)):
    """WebSocket endpoint for real-time resume updates"""
    
    # Authenticate user via token or user_id
    authenticated_user_id = None
    
    if token:
        try:
            # Decode token to get user_id
            payload = decode_token(token)
            if payload:
                authenticated_user_id = payload.get("sub")
                print(f"SUCCESS: WebSocket auth successful for user: {authenticated_user_id}")
            else:
                print(f"ERROR: WebSocket token decode failed - token may be expired")
                await websocket.close(code=4001, reason="Token expired or invalid")
                return
        except Exception as e:
            print(f"ERROR: WebSocket token decode error: {e}")
            await websocket.close(code=4003, reason="Invalid token")
            return
    elif user_id:
        # Use provided user_id (for backward compatibility)
        authenticated_user_id = user_id
    else:
        await websocket.close(code=4003, reason="Missing authentication")
        return
    
    if not authenticated_user_id:
        await websocket.close(code=4003, reason="Authentication failed")
        return
    
    await manager.connect(websocket, authenticated_user_id)
    connection_started = False
    try:
        # Send connection confirmation with error handling - but don't fail if connection closes immediately
        try:
            await asyncio.wait_for(
                websocket.send_text(json.dumps({"type": "connected", "message": "WebSocket connected"})),
                timeout=1.0  # 1 second timeout for initial message
            )
            connection_started = True
        except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK, RuntimeError):
            # Connection closed immediately - this is normal, client might be reconnecting
            # Don't log as error, just clean up and return
            manager.disconnect(websocket, authenticated_user_id)
            return
        except asyncio.TimeoutError:
            # Timeout sending initial message - connection might be slow
            manager.disconnect(websocket, authenticated_user_id)
            return
        except Exception as e:
            # Other errors - log but don't spam
            print(f"[WEBSOCKET] Error in connection setup for user {authenticated_user_id}: {type(e).__name__}")
            manager.disconnect(websocket, authenticated_user_id)
            return
        
        if not connection_started:
            return
        
        # Keep connection alive with ping/pong and handle messages
        last_ping_time = asyncio.get_event_loop().time()
        ping_interval = 30.0  # Send ping every 30 seconds
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while True:
            try:
                # Try to receive message with timeout
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=ping_interval
                    )
                    consecutive_errors = 0  # Reset error count on successful receive
                    
                    # Message received - echo back (if it's not a ping/pong)
                    try:
                        message_data = json.loads(data) if data else {}
                        if message_data.get("type") != "pong":
                            await websocket.send_text(json.dumps({"type": "echo", "message": f"Message received: {data}"}))
                    except json.JSONDecodeError:
                        # Not JSON, just echo as text
                        await websocket.send_text(json.dumps({"type": "echo", "message": f"Message received: {data}"}))
                    except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK, RuntimeError):
                        # Connection closed while sending - break out
                        break
                        
                except asyncio.TimeoutError:
                    # Timeout - send ping to keep connection alive
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_ping_time >= ping_interval:
                        try:
                            # Send ping message to keep connection alive
                            await websocket.send_text(json.dumps({"type": "ping", "timestamp": current_time}))
                            last_ping_time = current_time
                            consecutive_errors = 0  # Reset error count on successful ping
                        except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK, RuntimeError):
                            # Connection closed during ping - normal disconnect
                            break
                        except Exception as e:
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"[WEBSOCKET] Too many consecutive errors ({consecutive_errors}), closing connection")
                                break
                            await asyncio.sleep(0.5)  # Brief delay before retry
                        
            except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK, RuntimeError):
                # Normal connection close - exit gracefully
                break
            except WebSocketDisconnect:
                # Normal disconnect
                break
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"[WEBSOCKET] Too many consecutive errors ({consecutive_errors}) for user {authenticated_user_id}: {type(e).__name__}")
                    break
                # Brief delay before retry
                await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        # Normal disconnect - no need to log
        pass
    except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK):
        # Normal connection close - no need to log
        pass
    except Exception as e:
        # Only log unexpected exceptions
        print(f"[WEBSOCKET] Unexpected exception for user {authenticated_user_id}: {type(e).__name__}: {e}")
    finally:
        manager.disconnect(websocket, authenticated_user_id)
        # Only log cleanup if connection was actually started
        if connection_started:
            pass  # Don't spam logs for every disconnect


# Utility function to notify users (to be used by other routes)
async def notify_resume_update(resume_id: str, action: str, hr_user_id: str, manager_user_id: str = None):
    """Notify users about resume updates"""
    message = {
        "type": "resume_update",
        "resume_id": resume_id,
        "action": action,  # "shared", "status_changed", "created"
        "timestamp": "now"
    }
    
    message_json = json.dumps(message)
    
    # Notify HR user
    await manager.send_personal_message(message_json, hr_user_id)
    
    # Notify Manager if specified
    if manager_user_id:
        await manager.send_personal_message(message_json, manager_user_id)
