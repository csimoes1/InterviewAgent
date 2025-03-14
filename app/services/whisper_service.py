import asyncio
import logging
import tempfile
import os
from pathlib import Path

import numpy as np
import wave
from typing import Optional, Dict, Any
import aiohttp
import json

logger = logging.getLogger(__name__)

class WhisperService:
    """
    Service for transcribing audio using a whisper-server instance.
    This implementation connects to a whisper.cpp server running on HTTP.
    """

    def __init__(self,
                 server_url: str = "http://localhost:8080",
                 endpoint: str = "/inference",
                 temperature: float = 0.0,
                 temperature_inc: float = 0.2,
                 response_format: str = "json"):
        """
        Initialize the WhisperService with the server URL and parameters.

        Args:
            server_url: URL of the whisper-server
            endpoint: API endpoint for transcription
            temperature: Initial temperature parameter for sampling
            temperature_inc: Temperature increase parameter
            response_format: Response format (e.g., "json")
        """
        self.server_url = server_url
        self.endpoint = endpoint
        self.transcribe_url = f"{server_url}{endpoint}"
        self.temperature = temperature
        self.temperature_inc = temperature_inc
        self.response_format = response_format

        # Log initialization
        logger.info(f"WhisperService initialized with server URL: {self.server_url}")
        logger.info(f"Using transcription endpoint: {self.transcribe_url}")
        logger.info(f"Parameters: temperature={temperature}, temperature_inc={temperature_inc}, response_format={response_format}")

    async def transcribe(self, audio_data: bytes,
                         temperature: Optional[float] = None,
                         temperature_inc: Optional[float] = None,
                         response_format: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio data by sending it to the whisper-server.

        Args:
            audio_data: Raw audio data (PCM 16-bit, 16kHz, mono)
            temperature: Optional temperature parameter (overrides the default)
            temperature_inc: Optional temperature increase parameter (overrides the default)
            response_format: Optional response format (overrides the default)

        Returns:
            Dictionary containing the transcription result or None if transcription failed
        """
        if not audio_data:
            logger.warning("Empty audio data received")
            return None

        try:
            # Save audio data to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                self._save_as_wav(audio_data, temp_filename)

            logger.info(f"Saved audio to temporary file: {temp_filename}")

            # Send the WAV file to the server
            async with aiohttp.ClientSession() as session:
                # temp_filename = "/Users/csimoes/Projects/Python/InterviewAgent/whisper.cpp/samples/jfk.wav"
                logger.debug(f"temp_filename: {temp_filename}")
                with open(temp_filename, 'rb') as audio_file:
                    # Create form data with the WAV file and additional parameters
                    form_data = aiohttp.FormData()
                    form_data.add_field("file",
                                        open(temp_filename, "rb"),
                                        filename=Path(temp_filename).name,
                                        content_type="audio/wav")

                    # form_data.add_field('file',
                    #                     audio_file,
                    #                     filename='audio.wav',
                    #                     content_type='audio/wav')
                    # Use provided parameters or fall back to defaults
                    temp = str(temperature if temperature is not None else self.temperature)
                    temp_inc = str(temperature_inc if temperature_inc is not None else self.temperature_inc)
                    resp_format = response_format if response_format is not None else self.response_format

                    form_data.add_field('temperature', temp)
                    form_data.add_field('temperature_inc', temp_inc)
                    form_data.add_field('response_format', resp_format)

                    # Log request details
                    logger.info(f"Sending request to: {self.transcribe_url}")
                    logger.info(f"Request parameters: temperature={temp}, temperature_inc={temp_inc}, response_format={resp_format}")

                    # Log the start time
                    start_time = asyncio.get_event_loop().time()

                    async with session.post(self.transcribe_url, data=form_data) as response:
                        # Calculate and log request duration
                        duration = asyncio.get_event_loop().time() - start_time
                        logger.info(f"Request completed in {duration:.2f} seconds with status {response.status}")
                        # Check if request was successful
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Server returned error {response.status}: {error_text}")
                            logger.error(f"response={response}")
                            return None

                        # Get response content
                        content = await response.text()

                        try:
                            # Parse JSON response
                            result = json.loads(content)

                            # Log response details
                            logger.info(f"Received transcription result: {json.dumps(result, indent=2)}")
                            logger.info(f"Transcription: {result.get('text')}")

                            return result.get('text')
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse response as JSON. Raw response: {content[:500]}...")
                            return None

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error during transcription: {e}", exc_info=True)
            logger.error(f"Request details: URL={self.transcribe_url}, temp={temp}, temp_inc={temp_inc}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error in transcription: {e}", exc_info=True)
            return None
        finally:
            # Clean up temporary file
            os.unlink(temp_filename)
            logger.info(f"Temporary file {temp_filename} deleted")


    def _save_as_wav(self, audio_data: bytes, filename: str):
        """
        Save raw audio data as a WAV file.
        Assumes the input is 16-bit PCM at 16kHz mono.

        Args:
            audio_data: Raw audio data
            filename: Output WAV filename
        """
        try:
            # Log the audio data size
            logger.info(f"Converting {len(audio_data)} bytes of audio data to WAV format")

            # Convert raw audio data to numpy array
            # Assuming 16-bit PCM format
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Log audio properties
            duration = len(audio_array) / 16000  # in seconds
            logger.info(f"Audio duration: {duration:.2f} seconds ({len(audio_array)} samples at 16kHz)")

            # Create WAV file
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_array.tobytes())

            # Log file size
            file_size = os.path.getsize(filename)
            logger.info(f"WAV file created: {filename} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"Error saving WAV file: {e}", exc_info=True)
            raise

    async def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the whisper-server.

        Returns:
            Dictionary containing server information or None if request failed
        """
        try:
            info_url = f"{self.server_url}/info"
            logger.info(f"Requesting server info from: {info_url}")

            start_time = asyncio.get_event_loop().time()

            async with aiohttp.ClientSession() as session:
                async with session.get(info_url) as response:
                    duration = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Server info request completed in {duration:.2f} seconds with status {response.status}")

                    if response.status == 200:
                        content = await response.text()
                        try:
                            result = json.loads(content)
                            logger.info(f"Server info: {json.dumps(result, indent=2)}")
                            return result
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse server info as JSON: {e}")
                            logger.error(f"Raw response: {content[:500]}...")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get server info. Status: {response.status}")
                        logger.error(f"Error response: {error_text[:500]}...")
                        return None
        except Exception as e:
            logger.error(f"Error getting server info: {e}", exc_info=True)
            return None