import requests
import json
import os

# Get API key from environment variable (recommended for security)
# XAI_API_KEY = os.getenv("XAI_API_KEY")  # Set this in your environment, e.g., export XAI_API_KEY='your_key_here'
XAI_API_KEY = ""
if not XAI_API_KEY:
    raise ValueError("Please set the XAI_API_KEY environment variable")

# API endpoint
url = "https://api.x.ai/v1/chat/completions"

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {XAI_API_KEY}"
}

# Request payload
payload = {
    "model": "grok-2-latest",
    "messages": [
        {
            "role": "system",
            "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
        },
        {
            "role": "user",
            "content": "What do you get when you combine yellow and blue?"
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