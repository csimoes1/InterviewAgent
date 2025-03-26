import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.routes.websocket import router as websocket_router
from app.routes.api import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WebRTC Speech-to-Text with Grok",
    description="A web application that processes speech using WebRTC and whisper.cpp, then sends it to Grok API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket_router)
app.include_router(api_router)

# Mount static files
app.mount("/lexllm", StaticFiles(directory="lexllm"), name="lexllm")
app.mount("/", StaticFiles(directory="lexllm", html=True), name="root")

if __name__ == "__main__":
    logger.info("Starting server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)