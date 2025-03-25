import requests
import json
import os

from app.main import logger

# Get API key from environment variable (recommended for security)
XAI_API_KEY = os.getenv("XAI_API_KEY")  # Set this in your environment, e.g., export XAI_API_KEY='your_key_here'
if not XAI_API_KEY:
    raise ValueError("Please set the XAI_API_KEY environment variable")

# API endpoint
url = "https://api.x.ai/v1/chat/completions"

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {XAI_API_KEY}"
}

file_path = "/Users/csimoes/Projects/Python/InterviewAgent/mortenmo.txt"
system_prompt = ""
try:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            system_prompt = file.read().strip()
    else:
        logger.warning(f"System prompt file {file_path} not found, using default")

except Exception as e:
    logger.error(f"Error loading system prompt from {file_path}: {e}", exc_info=True)



# Request payload
payload = {
    "model": "grok-2-latest",
    "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": "Write me 3 sentences summarizing the experience of Morten Moeller using the resume passed in the system prompt."
        }
    ],
    "stream": False,
    "temperature": 0
}

# Make the API request
try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Check if the request was successful
    response.raise_for_status()

    # Parse and print the response
    result = response.json()
    print(json.dumps(result, indent=2))

except requests.exceptions.HTTPError as err:
    print(f"HTTP error occurred: {err}")
    if response.text:
        print(f"Response details: {response.text}")
except Exception as e:
    print(f"An error occurred: {e}")

