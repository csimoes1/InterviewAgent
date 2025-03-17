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
grok_service = GrokService()

# Active connections
websocket_connections: Dict[str, WebSocket] = {}

# Conversation histories for each connection
conversation_histories: Dict[str, List[Dict]] = {}

# this is where we receive the audio data from the client
@router.websocket("/ws/audio")
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

                            # Get response from Grok service
                            grok_response = await grok_service.get_response(
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