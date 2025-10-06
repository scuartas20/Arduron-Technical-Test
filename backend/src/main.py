# FastAPI application entry point
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from routes.api_routes import api_router
from websocket.websocket_manager import websocket_manager, handle_websocket_message

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)

@app.get("/")
async def root():
    return {
        "message": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "endpoints": {
            "api": settings.api_prefix,
            "websocket": settings.ws_endpoint,
            "health": f"{settings.api_prefix}/health",
            "docs": "/docs"
        }
    }

@app.websocket(settings.ws_endpoint)
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            # Handle the message
            await handle_websocket_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.reload
    )