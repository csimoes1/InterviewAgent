import os
import aiohttp
import logging
from typing import Dict, List, Optional

from app.services.user_service import get_user_by_email

logger = logging.getLogger(__name__)

class GrokService:
    PROMPT_DIR = "prompts/"  # Directory where system prompt files are stored

    """
    Service for interacting with the Grok (X.AI) API.
    Manages API requests and conversation context.
    """

    def __init__(self, email=""):
        """
        Initialize the GrokService with API credentials and system prompt from file.

        Args:
            system_prompt_file: Path to the file containing the system prompt
        """
        self.system_prompt_file = self.PROMPT_DIR + "systemPrompt.txt"
        self.resume = ""
        self.name = ""
        if(email):
            self.name = get_user_by_email(email)
            logger.info(f"Retrieved name for email '{email}': {self.name}")
            # to get the resume file for the specific user trim everything before the @ sign
            email_prefix = email.split('@')[0]
            resume_file = f"{self.PROMPT_DIR}{email_prefix}.txt"
            self.resume = self._load_system_prompt(resume_file)

        logger.info(f"system_prompt_file: {self.system_prompt_file}")
        logger.info(f"resume file: {self.resume}")

        self.api_key = os.environ.get("GROK_API_KEY")
        if not self.api_key:
            logger.warning("GROK_API_KEY not set in environment variables")

        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.model = os.environ.get("GROK_MODEL", "grok-2-latest")

        # Load system prompt from file
        temp_str = self._load_system_prompt(self.system_prompt_file)
        # replace placeholder with name in system prompt
        self.preamble = temp_str.replace("[NAME_HERE]", self.name)

        self.system_prompt = self.preamble + "\\n" + self.resume

        logger.info(f"GrokService initialized with model: {self.model}")
        logger.info(f"System prompt loaded: {self.system_prompt[:50]}..." if self.system_prompt else "No system prompt loaded")

    def _load_system_prompt(self, file_path: str) -> str:
        """
        Load the system prompt from a file.

        Args:
            file_path: Path to the system prompt file

        Returns:
            The system prompt string, or a default if file doesn't exist
        """
        default_prompt = ""

        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                    if content:
                        logger.info(f"Successfully loaded system prompt from {file_path}")
                        return content
                    else:
                        logger.warning(f"System prompt file {file_path} is empty, using default")
                        return default_prompt
            else:
                logger.warning(f"System prompt file {file_path} not found, using default")
                return default_prompt
        except Exception as e:
            logger.error(f"Error loading system prompt from {file_path}: {e}", exc_info=True)
            return default_prompt

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
        logger.debug("user_message: " + user_message)
        if not self.api_key:
            return "Error: API key not configured. Please set the GROK_API_KEY environment variable."

        try:
            # Prepare messages with history
            messages = []

            # if conversation history is getting longer than n messages, tell system to wrap it up
            if conversation_history and len(conversation_history) > 4:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt + " Try to end the interview gracefully and then summarize the conversation with a 2 sentence summary.  Finally end with a quote related to this conversation and be sure to cite the author of the quote."
                })
            elif conversation_history and len(conversation_history) > 6:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt + " End the interview now saying 'I'm sorry but we are out of time'.  Thank the guest and provide a quote related to this conversation and be sure to cite the author of the quote."
                })



            # Add system message for context
            messages.append({
                "role": "system",
                "content": self.system_prompt
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
