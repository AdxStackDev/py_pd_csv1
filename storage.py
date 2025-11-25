"""
Redis connection helper for Vercel KV storage.
Provides fallback to in-memory storage for local development.
"""
import os
import json
import logging
from typing import Optional, Dict, Any

# Try to import redis, but don't fail if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Using in-memory storage.")

# In-memory fallback storage
_memory_store: Dict[str, str] = {}

class StorageClient:
    """Unified storage client that uses Redis on Vercel, in-memory locally."""
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        
        # Check if we're on Vercel and Redis is configured
        redis_url = os.getenv("REDIS_URL") or os.getenv("KV_URL")
        
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logging.info("✅ Connected to Redis (Vercel KV)")
            except Exception as e:
                logging.warning(f"Failed to connect to Redis: {e}. Using in-memory storage.")
                self.redis_client = None
                self.use_redis = False
        else:
            logging.info("📦 Using in-memory storage (local development)")
    
    def get(self, key: str) -> Optional[str]:
        """Get value from storage."""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.get(key)
            else:
                return _memory_store.get(key)
        except Exception as e:
            logging.error(f"Error getting key {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set value in storage.
        
        Args:
            key: Storage key
            value: Value to store (string)
            ex: Expiration time in seconds (optional)
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.set(key, value, ex=ex)
                return True
            else:
                _memory_store[key] = value
                return True
        except Exception as e:
            logging.error(f"Error setting key {key}: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value from storage."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON for key {key}: {e}")
                return None
        return None
    
    def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """Set JSON value in storage."""
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, ex=ex)
        except Exception as e:
            logging.error(f"Error encoding JSON for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from storage."""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
                return True
            else:
                if key in _memory_store:
                    del _memory_store[key]
                return True
        except Exception as e:
            logging.error(f"Error deleting key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                return key in _memory_store
        except Exception as e:
            logging.error(f"Error checking key {key}: {e}")
            return False

# Global storage client instance
storage = StorageClient()
