import os
import aiohttp
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GrokService:
    """
    Service for interacting with the Grok (X.AI) API.
    Manages API requests and conversation context.
    """

    def __init__(self):
        """
        Initialize the GrokService with API credentials.
        """
        self.api_key = os.environ.get("GROK_API_KEY")
        if not self.api_key:
            logger.warning("GROK_API_KEY not set in environment variables")

        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.model = os.environ.get("GROK_MODEL", "grok-2-latest")

        logger.info(f"GrokService initialized with model: {self.model}")

    async def get_response(self,
                           user_message: str,
                           conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Get a response from the Grok API for the user message.

        Args:
            user_message: The user's transcribed message
            conversation_history: Optional conversation history for context

        Returns:
            The AI's response text
        """
        if not self.api_key:
            return "Error: API key not configured. Please set the GROK_API_KEY environment variable."

        try:
            # Prepare messages with history
            messages = []

            # Add system message for context
            messages.append({
                "role": "system",
                "content": "You are a helpful voice assistant. Respond concisely and clearly as your responses will be read aloud."
            })

            # Add conversation history if available
            if conversation_history:
                for message in conversation_history:
                    messages.append(message)
            else:
                # If no history, just add the current message
                messages.append({
                    "role": "user",
                    "content": user_message
                })

            # Prepare API request
            request_data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150  # Keep responses concise for voice interaction
            }

            logger.info(f"Sending request to Grok API: {request_data}")

            # Make API request
            async with aiohttp.ClientSession() as session:
                logger.debug(f"request_data={request_data}")
                async with session.post(
                        self.api_url,
                        json=request_data,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Grok API error response {response}")
                        logger.error(f"Grok API error ({response.status}): {error_text}")
                        return f"I'm sorry, there was an error communicating with the AI service. Status code: {response.status}"

                    response_data = await response.json()

                    # Extract the response content
                    if (response_data.get("choices") and
                            len(response_data["choices"]) > 0 and
                            response_data["choices"][0].get("message") and
                            response_data["choices"][0]["message"].get("content")):

                        content = response_data["choices"][0]["message"]["content"]
                        logger.info(f"Received response from Grok API: {content}")
                        return content
                    else:
                        logger.error(f"Unexpected response format: {response_data}")
                        return "I'm sorry, there was an error processing the response from the AI service."

        except Exception as e:
            logger.error(f"Error calling Grok API: {e}", exc_info=True)
            return f"I'm sorry, there was an error: {str(e)}"

'''
Example Response:
{
  "id": "3cc399d8-7ad4-4f97-9914-af902b3ee1e0",
  "object": "chat.completion",
  "created": 1741978502,
  "model": "grok-2-1212",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "When you combine yellow and blue, you get green. It's like mixing the tranquility of a clear blue sky with the warmth of a sunny yellow day, resulting in the vibrant and refreshing color of green. Just imagine a lush green meadow or the leaves of a tree, and you'll see the beauty of this combination. So, go ahead and mix those colors, and let the magic of green unfold before your eyes!",
        "refusal": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 39,
    "completion_tokens": 85,
    "reasoning_tokens": 0,
    "total_tokens": 124,
    "prompt_tokens_details": {
      "text_tokens": 39,
      "audio_tokens": 0,
      "image_tokens": 0,
      "cached_tokens": 0
    }
  },
  "system_fingerprint": "fp_fe9e7ef66e"
}
 
'''