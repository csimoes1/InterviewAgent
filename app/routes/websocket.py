import asyncio
import base64
import json
import logging
import uuid
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.vad import VoiceActivityDetector
from app.services.whisper_service import WhisperService
from app.services.grok_service import GrokService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
whisper_service = WhisperService()
# We'll initialize GrokService instances per connection, based on user email

# Active connections
websocket_connections: Dict[str, WebSocket] = {}

# Conversation histories for each connection
conversation_histories: Dict[str, List[Dict]] = {}

# Store GrokService instances for each connection
grok_services: Dict[str, GrokService] = {}

# User info for each connection
user_info: Dict[str, Dict] = {}

# this is where we receive the audio data from the client
@router.websocket("/lexllm/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for audio streaming.
    Receives audio chunks, processes them with VAD detection,
    transcribes with whisper.cpp when speech ends,
    sends transcription to Grok API, and returns the response.
    """
    # Accept the connection
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    websocket_connections[connection_id] = websocket
    conversation_histories[connection_id] = []
    user_info[connection_id] = {"email": None, "name": None}

    # Initialize VAD detector
    vad_detector = VoiceActivityDetector()

    try:
        logger.info(f"New WebSocket connection established: {connection_id}")

        # Send initial message
        await websocket.send_json({
            "type": "info",
            "message": "Connection established. Start speaking."
        })

        # Audio buffer for accumulating chunks
        audio_buffer = bytearray()

        # continuously receive audio data from the client
        while True:
            # Receive message
            data = await websocket.receive()

            if "text" in data:
                message = json.loads(data["text"])

                # Handle different message types
                if message["type"] == "audio":
                    # Decode base64 audio data
                    audio_chunk = base64.b64decode(message["data"])

                    # Process with VAD (only process the new chunk, not the entire buffer)
                    speech_ended, speech_frames = vad_detector.process_audio(audio_chunk)

                    # If speech has ended, process it
                    if speech_ended and speech_frames:
                        logger.info(f"Speech detected and ended, sending to whisper len={len(speech_frames)}")

                        await websocket.send_json({
                            "type": "status",
                            "message": "Processing audio..."
                        })

                        # Process audio with Whisper
                        transcription = await whisper_service.transcribe(speech_frames)

                        if transcription:
                            # Send transcription to client
                            await websocket.send_json({
                                "type": "transcription",
                                "text": transcription
                            })

                            # Update conversation history
                            conversation_histories[connection_id].append({
                                "role": "user",
                                "content": transcription
                            })

                            # Get response from Grok API
                            await websocket.send_json({
                                "type": "status",
                                "message": "Getting response from AI..."
                            })

                            logger.debug("websocket.py: get_grok_service.get_response about to be called")
                            # Get response from appropriate Grok service
                            grok_response = await get_grok_service(connection_id).get_response(
                                transcription,
                                conversation_histories[connection_id]
                            )

                            # Update conversation history with AI response
                            conversation_histories[connection_id].append({
                                "role": "assistant",
                                "content": grok_response
                            })

                            # Send AI response to client
                            await websocket.send_json({
                                "type": "ai_response",
                                "text": grok_response
                            })

                        # VAD detector has already been reset in process_audio

                elif message["type"] == "reset":
                    # Reset the conversation and VAD detector
                    conversation_histories[connection_id] = []
                    vad_detector.reset()
                    await websocket.send_json({
                        "type": "info",
                        "message": "Conversation reset."
                    })

                elif message["type"] == "user_info":
                    # Store user info and initialize personalized Grok service
                    user_email = message.get("email")
                    user_name = message.get("name")

                    if user_email:
                        user_info[connection_id]["email"] = user_email
                        user_info[connection_id]["name"] = user_name

                        # Initialize a new GrokService with the user's email
                        initialize_grok_service(connection_id, user_email)

                        logger.info(f"Initialized personalized GrokService for user: {user_email}")

                        # Send confirmation
                        await websocket.send_json({
                            "type": "info",
                            "message": f"Personalized settings loaded for {user_name or user_email}"
                        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]
        if connection_id in conversation_histories:
            del conversation_histories[connection_id]
        if connection_id in grok_services:
            del grok_services[connection_id]
        if connection_id in user_info:
            del user_info[connection_id]


def initialize_grok_service(connection_id: str, user_email: str):
    """
    Initialize a new GrokService instance for the given connection and user email.

    Args:
        connection_id: The unique identifier for the WebSocket connection
        user_email: The user's email address
    """
    # Create a new GrokService instance with the user's email
    grok_services[connection_id] = GrokService(email=user_email)


def get_grok_service(connection_id: str) -> GrokService:
    """
    Get the GrokService instance for the given connection ID.
    If none exists, create a default one.

    Args:
        connection_id: The unique identifier for the WebSocket connection

    Returns:
        The appropriate GrokService instance
    """
    if connection_id not in grok_services:
        # Create a default service if none exists
        grok_services[connection_id] = GrokService()

    return grok_services[connection_id]