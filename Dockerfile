FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    git \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Link python3 to python for convenience (optional)
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set working directory and copy files
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Debug line
RUN ls -la /app  # See what's copied

# Build whisper.cpp from its subdirectory
WORKDIR /app/whisper.cpp
RUN cmake -B build && cmake --build build --config Release

# Download Whisper model
WORKDIR /app
RUN mkdir -p /app/whisper_models
RUN wget -O /app/whisper_models/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

# Switch back to /app for the app runtime
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV WHISPER_MODEL_PATH=/app/whisper_models/ggml-base.en.bin
ENV WHISPER_CPP_PATH=/app/whisper.cpp/build/bin/whisper-cli

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]