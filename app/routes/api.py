from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.grok_service import GrokService
from app.services.user_service import get_user_by_email

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

class IntroductionRequest(BaseModel):
    email: str
    messages: List[Message]

class UserResponse(BaseModel):
    email: str
    name: str


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

        logger.debug("api.py grok_service.get_response about to be called")
        # Get response from Grok API
        response = await grok_service.get_response(last_user_message, messages)

        return ConversationResponse(response=response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/introduction", response_model=ConversationResponse)
async def get_introduction(request: IntroductionRequest):
    """
    Get a personalized introduction from the Grok API.

    Args:
        request: The request with user email and optional name

    Returns:
        A personalized introduction
    """
    logger.debug("get_introduction request: " + str(request))
    try:
        # Create GrokService with user's email
        grok_service = GrokService(email=request.email)

        # Construct the prompt for the introduction
        # prompt = "Write a 3 sentence introduction"
        # if request.name:
        #     prompt = f"Write a 3 sentence introduction for {request.name}"

        # Get response from Grok API
        logger.debug(f"About to call GrokService.get_response with request.messages ${request.messages}")
        response = await grok_service.get_response(request.messages[0].content)

        return ConversationResponse(response=response)

    except Exception as e:
        logger.error(f"Error getting introduction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user", response_model=UserResponse)
async def get_user(email: str):
    """
    Get user name by email.

    Args:
        email: The email address to look up

    Returns:
        The email and user name if found, or null if not found
    """
    try:
        name = get_user_by_email(email)
        return UserResponse(email=email, name=name)
    except Exception as e:
        logger.error(f"Error in get_user endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))