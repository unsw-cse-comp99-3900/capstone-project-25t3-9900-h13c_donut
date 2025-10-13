"""
Authentication dependencies for WebSocket connections
"""

from fastapi import HTTPException, status
from jose import jwt, JWTError
from typing import Dict, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

async def get_current_user_websocket(token: Optional[str]) -> Dict:
    """
    Authenticate user from JWT token for WebSocket connections
    
    Args:
        token: JWT token string
        
    Returns:
        Dict containing user information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is required for WebSocket authentication"
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user information
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Return user info (in real implementation, you might fetch from database)
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "username": payload.get("username"),
            "is_admin": payload.get("is_admin", False)
        }
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


