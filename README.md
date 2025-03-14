# WebRTC Speech-to-Text with Grok API

This project provides a web application that uses WebRTC to capture audio from the user's microphone, processes it with whisper.cpp for speech-to-text conversion, and integrates with X.AI's Grok API for intelligent responses.

## Features

- Real-time audio capture using WebRTC
- Server-side speech-to-text processing with whisper.cpp
- Integration with X.AI's Grok API
- WebSocket-based communication for real-time interactions
- Simple and intuitive user interface

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- X.AI (Grok) API key

## Setup and Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/webrtc-whisper-grok.git
   cd webrtc-whisper-grok
   ```

2. Create a `.env` file in the project root with your API key:
   ```
   GROK_API_KEY=your_api_key_here
   ```

3. Build and start the application with Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Access the application at http://localhost:8000

## Manual Setup (without Docker)

If you prefer to run the application without Docker:

1. Install system dependencies:
    - Python 3.10+
    - FFmpeg
    - Build tools (gcc, cmake, etc.)

2. Clone and build whisper.cpp:
   ```bash
   git clone https://github.com/ggerganov/whisper.cpp.git
   cd whisper.cpp
   make
   bash ./models/download-ggml-model.sh base.en
   cd ..
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables:
   ```bash
   export GROK_API_KEY=your_api_key_here
   export WHISPER_CPP_PATH=/path/to/whisper.cpp/main
   ```

5. Run the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Architecture

- **Frontend**: HTML/CSS/JavaScript with WebRTC for audio capture
- **Backend**: FastAPI Python application
- **WebSockets**: For real-time audio streaming and response delivery
- **Processing Pipeline**: Audio → whisper.cpp → Grok API → User Interface

## Development

The project structure follows a clean architecture approach:

- `/app`: Backend Python code
- `/static`: Frontend assets
- `/tests`: Test cases

## Security Considerations

- This application requires microphone access, which is sensitive permission
- HTTPS should be used in production to secure the WebRTC connection
- API keys should be properly secured and not exposed in client-side code

## License

[MIT License](LICENSE)

## Acknowledgements

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for high-performance speech recognition
- X.AI for the Grok API
- FastAPI for the web framework