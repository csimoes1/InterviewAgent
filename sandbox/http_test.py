import aiohttp
import asyncio
from pathlib import Path

class WhisperClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.endpoint = f"{self.base_url}/inference"

    async def transcribe_audio(self, file_path: str, temperature: float = 0.0, temperature_inc: float = 0.2):
        """
        Send an audio file to the whisper.cpp server and return the transcription.

        Args:
            file_path (str): Path to the audio file (e.g., WAV format)
            temperature (float): Temperature parameter for transcription (default: 0.0)
            temperature_inc (float): Temperature increment (default: 0.2)

        Returns:
            dict: JSON response containing the transcription
        """
        # Prepare the form data
        form_data = aiohttp.FormData()
        form_data.add_field("file",
                            open(file_path, "rb"),
                            filename=Path(file_path).name,
                            content_type="audio/wav")
        form_data.add_field("temperature", str(temperature))
        form_data.add_field("temperature_inc", str(temperature_inc))
        form_data.add_field("response_format", "json")

        # Create an aiohttp session
        async with aiohttp.ClientSession() as session:
            # Send the POST request
            async with session.post(self.endpoint, data=form_data) as response:
                if response.status == 200:
                    # Return the JSON response
                    return await response.json()
                else:
                    # Handle errors
                    error_text = await response.text()
                    raise Exception(f"Request failed with status {response.status}: {error_text}")

# Example usage
async def main():
    # Initialize the client
    client = WhisperClient(base_url="http://localhost:8080")

    # Specify the file path
    file_path = "/whisper.cpp/samples/jfk.wav"

    try:
        # Call the transcription method
        result = await client.transcribe_audio(file_path, temperature=0.0, temperature_inc=0.2)
        print("Transcription:", result.get("text", "No transcription found"))
    except Exception as e:
        print(f"Error: {e}")

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())