from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.grok_service import GrokService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# Initialize services
grok_service = GrokService()

# Models
class Message(BaseModel):
    role: str
    content: str

class ConversationRequest(BaseModel):
    messages: List[Message]

class ConversationResponse(BaseModel):
    response: str

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok"}

@router.post("/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest):
    """
    Chat endpoint for non-WebSocket communication.
    Useful for testing or fallback.

    Args:
        request: The conversation request with message history

    Returns:
        The AI's response
    """
    try:
        # Convert Pydantic models to dictionaries
        messages = [msg.dict() for msg in request.messages]

        # Get the last user message
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message provided")

        last_user_message = user_messages[-1]["content"]

        # Get response from Grok API
        response = await grok_service.get_response(last_user_message, messages)

        return ConversationResponse(response=response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))