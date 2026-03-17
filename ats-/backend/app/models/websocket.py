from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class WebSocketConnectionModel(BaseModel):
    """WebSocket connection tracking model"""
    id: Optional[str] = Field(None, alias="_id")
    
    # Connection details
    user_id: str
    connection_id: str  # Unique identifier for this connection
    socket_id: Optional[str] = None
    
    # Connection metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    room: Optional[str] = None  # For grouping connections
    
    # Status
    status: str = "connected"  # "connected", "disconnected", "error"
    last_ping: Optional[datetime] = None
    
    # Timestamps
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    disconnected_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class WebSocketMessageModel(BaseModel):
    """WebSocket message log model"""
    id: Optional[str] = Field(None, alias="_id")
    
    # Message details
    message_type: str  # "resume_update", "status_change", "notification"
    message_data: Dict[str, Any]
    
    # Routing information
    sender_id: Optional[str] = None
    recipient_id: Optional[str] = None
    broadcast: bool = False
    
    # Delivery status
    delivery_status: str = "sent"  # "sent", "delivered", "failed"
    delivery_attempts: int = 1
    error_message: Optional[str] = None
    
    # Timestamps
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
