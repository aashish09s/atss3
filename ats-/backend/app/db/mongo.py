from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global client instance
_client: AsyncIOMotorClient = None


async def get_client() -> AsyncIOMotorClient:
    """Get MongoDB client instance"""
    global _client
    if _client is None:
        try:
            _client = AsyncIOMotorClient(settings.mongodb_uri)
            # Test connection
            await _client.admin.command('ping')
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Return None to handle gracefully
            _client = None
    return _client


async def get_db():
    """Get database instance"""
    client = await get_client()
    if client is None:
        logger.error("Cannot get database - MongoDB connection failed")
        return None
    return client.hirepy
