"""
FastAPI WebSocket Server for Real-time Accent Translation
Main application entry point
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.websocket.manager import WebSocketManager
from app.websocket.handlers import WebSocketHandler
from app.auth.dependencies import get_current_user_websocket
from app.models.responses import ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting FastAPI WebSocket server...")
    yield
    logger.info("Shutting down FastAPI WebSocket server...")

# Create FastAPI application
app = FastAPI(
    title="Fast Accent Translator WebSocket API",
    description="Real-time WebSocket API for accent translation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "websocket-server"}

@app.websocket("/ws/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = None,
    token: str = None
):
    """
    WebSocket endpoint for real-time audio processing
    
    Args:
        websocket: WebSocket connection
        session_id: Optional session ID for resuming
        token: JWT token for authentication
    """
    handler = WebSocketHandler(websocket_manager)
    
    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted")
        
        # Authenticate user
        try:
            user = await get_current_user_websocket(token)
            logger.info(f"User authenticated: {user.get('user_id')}")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            await websocket.send_json({
                "type": "error",
                "error": "Authentication failed",
                "code": "AUTH_ERROR"
            })
            await websocket.close(code=1008)  # Policy violation
            return
        
        # Handle WebSocket communication
        await handler.handle_connection(websocket, user, session_id)
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error", 
                "error": str(e),
                "code": "INTERNAL_ERROR"
            })
        except:
            pass  # Connection might be closed
    finally:
        # Cleanup
        await websocket_manager.disconnect(websocket)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Internal server error",
            requestId="unknown",
            timestamp=None
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

