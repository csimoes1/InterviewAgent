/**
 * WebRTC Audio Capture and Processing
 * Handles microphone access, audio processing, and WebSocket communication
 */

class AudioHandler {
    constructor() {
        // Configuration
        this.audioContext = null;
        this.mediaStream = null;
        this.recorder = null;
        this.websocket = null;
        this.isRecording = false;
        this.processor = null;
        // this.websocketUrl = `ws://${window.location.host}/ws/audio`;
        this.websocketUrl = `ws://localhost:8000/ws/audio`;

        // Audio processing parameters
        this.sampleRate = 16000; // Target sample rate for whisper
        this.bufferSize = 4096;  // Buffer size for audio processing

        // User information
        const lsEmail = localStorage.getItem('userEmail');
        const lsName = localStorage.getItem('userName');

        // this.log(`lsEmail=${lsEmail} lsName=${lsName}`);

        this.userInfo = {
            email: lsEmail,
            name: lsName
        };

        // Event callbacks
        this.onStatusChange = null;
        this.onTranscription = null;
        this.onAIResponse = null;
        this.onError = null;

        // Logging settings
        this.isDebugMode = true;
        this.audioProcessCounter = 0;
        this.lastLogTime = 0;
        this.logInterval = 2000; // Log every 2 seconds to avoid console spam

        console.log("🎙️ AudioHandler initialized");
    }

    /**
     * Set user information
     * @param {Object} userInfo - User information object with name and email properties
     */
    setUserInfo(userInfo) {
        if (userInfo && typeof userInfo === 'object') {
            this.userInfo.name = userInfo.name || null;
            this.userInfo.email = userInfo.email || null;

            this.log(`User info set: ${this.userInfo.name} (${this.userInfo.email})`, true);

            // If already connected to WebSocket, send user info
            this.sendUserInfoToServer();
        }
    }

    /**
     * Send user information to the server
     */
    sendUserInfoToServer() {
        this.log(`Sending user info to server email=${this.userInfo.email} name=${this.userInfo.name}`);
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN && this.userInfo.email) {
            this.log(`Sending user info to server: ${this.userInfo.email}`);

            this.websocket.send(JSON.stringify({
                type: 'user_info',
                email: this.userInfo.email,
                name: this.userInfo.name
            }));
        }
    }

    /**
     * Enhanced console logging function
     */
    log(message, force = false) {
        if (this.isDebugMode || force) {
            console.log(`🎙️ ${new Date().toISOString().substring(11, 19)} - ${message}`);
        }
    }

    /**
     * Initialize audio context and request microphone access
     */
    async initialize() {
        try {
            this.log("Initializing audio context and requesting microphone access...");

            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.log(`Audio context created with sample rate: ${this.audioContext.sampleRate}Hz`);

            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                },
                video: false
            });

            this.log("✅ Microphone access granted");

            // Get audio track info
            const audioTracks = this.mediaStream.getAudioTracks();
            if (audioTracks.length > 0) {
                const settings = audioTracks[0].getSettings();
                this.log(`Microphone settings: ${JSON.stringify(settings)}`, true);
            }

            return true;
        } catch (error) {
            this.log(`❌ Error initializing audio: ${error.message}`, true);
            console.error('Error initializing audio:', error);
            if (this.onError) {
                this.onError('Could not access microphone. Please ensure you have granted permission.');
            }
            return false;
        }
    }

    /**
     * Connect to WebSocket server
     */
    connectWebSocket() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.log("WebSocket already connected");
            return; // Already connected
        }

        this.log(`Connecting to WebSocket server at ${this.websocketUrl}...`);

        this.websocket = new WebSocket(this.websocketUrl);

        this.websocket.onopen = () => {
            this.log("✅ WebSocket connected", true);

            // Send user info if available
            this.sendUserInfoToServer();

            if (this.onStatusChange) {
                this.onStatusChange('Connected');
            }
        };

        this.websocket.onclose = () => {
            this.log("WebSocket disconnected");
            if (this.onStatusChange) {
                this.onStatusChange('Disconnected');
            }
        };

        this.websocket.onerror = (error) => {
            this.log(`❌ WebSocket error: ${error}`, true);
            console.error('WebSocket error:', error);
            if (this.onError) {
                this.onError('Connection error. Please try again.');
            }
        };

        this.websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                switch (message.type) {
                    case 'transcription':
                        this.log(`📝 Received transcription: "${message.text}"`, true);
                        if (this.onTranscription) {
                            this.onTranscription(message.text);
                        }
                        break;

                    case 'ai_response':
                        this.log(`🤖 Received AI response: "${message.text}"`, true);
                        if (this.onAIResponse) {
                            this.onAIResponse(message.text);
                        }
                        break;

                    case 'status':
                    case 'info':
                        this.log(`ℹ️ Server status: ${message.message}`);
                        if (this.onStatusChange) {
                            this.onStatusChange(message.message);
                        }
                        break;

                    case 'error':
                        this.log(`❌ Server error: ${message.message}`, true);
                        if (this.onError) {
                            this.onError(message.message);
                        }
                        break;
                }
            } catch (error) {
                this.log(`❌ Error parsing WebSocket message: ${error.message}`, true);
                console.error('Error parsing WebSocket message:', error);
            }
        };
    }

    /**
     * Start recording audio
     */
    async startRecording() {
        if (this.isRecording) {
            this.log("Already recording");
            return; // Already recording
        }

        try {
            this.log("Starting audio recording...");

            // Make sure we're initialized and connected
            if (!this.mediaStream) {
                this.log("Media stream not initialized, initializing now...");
                const initialized = await this.initialize();
                if (!initialized) return;
            }

            this.connectWebSocket();

            // Create audio source from media stream
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.log("Audio source created from media stream");

            // Create script processor for audio processing
            this.processor = this.audioContext.createScriptProcessor(this.bufferSize, 1, 1);
            this.log(`Script processor created with buffer size: ${this.bufferSize}`);

            // Connect source -> processor -> destination
            source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
            this.log("Audio processing pipeline connected");

            // Reset counters
            this.audioProcessCounter = 0;
            this.lastLogTime = Date.now();

            // Process audio
            this.processor.onaudioprocess = (e) => {
                if (!this.isRecording || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                    return;
                }

                // Count processing events
                this.audioProcessCounter++;

                // Periodic logging to avoid flooding the console
                const now = Date.now();
                if (now - this.lastLogTime > this.logInterval) {
                    this.log(`Processing audio: ${this.audioProcessCounter} chunks processed in the last ${this.logInterval/1000}s`);
                    this.audioProcessCounter = 0;
                    this.lastLogTime = now;
                }

                // Get audio data from input buffer
                const inputBuffer = e.inputBuffer;
                const inputData = inputBuffer.getChannelData(0);

                // Check for sound activity (simple amplitude check)
                const audioLevel = this.getAudioLevel(inputData);
                if (audioLevel > 0.01) {
                    // Only log if there's significant sound
                    this.log(`🔊 Audio activity detected! Level: ${audioLevel.toFixed(4)}`);
                }

                // Resample if necessary (web audio API might use a different sample rate)
                const audioData = this.resampleIfNeeded(inputData, inputBuffer.sampleRate);

                // Convert to 16-bit PCM (whisper expects 16-bit PCM)
                const pcmData = this.floatTo16BitPCM(audioData);

                // Send audio data to server
                this.sendAudioChunk(pcmData);
            };

            this.isRecording = true;
            this.log("✅ Recording started", true);

            if (this.onStatusChange) {
                this.onStatusChange('Recording');
            }

            return true;
        } catch (error) {
            this.log(`❌ Error starting recording: ${error.message}`, true);
            console.error('Error starting recording:', error);
            if (this.onError) {
                this.onError('Could not start recording: ' + error.message);
            }
            return false;
        }
    }

    /**
     * Calculate audio level (amplitude) of the signal
     */
    getAudioLevel(audioData) {
        // Calculate RMS (Root Mean Square) of the audio buffer
        let sum = 0;
        for (let i = 0; i < audioData.length; i++) {
            sum += audioData[i] * audioData[i];
        }
        const rms = Math.sqrt(sum / audioData.length);
        return rms;
    }

    /**
     * Stop recording audio
     */
    stopRecording() {
        if (!this.isRecording) {
            return;
        }

        this.log("Stopping audio recording...");
        this.isRecording = false;

        // Disconnect audio processor
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
            this.log("Audio processor disconnected");
        }

        this.log("✅ Recording stopped", true);

        if (this.onStatusChange) {
            this.onStatusChange('Stopped');
        }
    }

    /**
     * Reset conversation
     */
    resetConversation() {
        this.log("Resetting conversation...");
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'reset'
            }));
            this.log("Reset message sent to server");
        }
    }

    /**
     * Close connection and clean up resources
     */
    close() {
        this.log("Closing AudioHandler and cleaning up resources...");
        this.stopRecording();

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => {
                track.stop();
                this.log(`Stopped media track: ${track.kind}`);
            });
            this.mediaStream = null;
        }

        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
            this.log("WebSocket connection closed");
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
            this.log("Audio context closed");
        }

        this.log("✅ AudioHandler closed and resources cleaned up", true);
    }

    /**
     * Send audio chunk to server via WebSocket
     */
    sendAudioChunk(audioData) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            this.log("ERROR: WebSocket not connected, cannot send audio");
            return;
        }

        // Convert audio data to base64
        const base64Data = this.arrayBufferToBase64(audioData.buffer);

        // Send to server
        this.websocket.send(JSON.stringify({
            type: 'audio',
            data: base64Data
        }));

        // Don't log every send to avoid console spam
        // Instead we use the counter in the onaudioprocess handler
    }

    /**
     * Resample audio if the sample rate is different from target
     */
    resampleIfNeeded(audioData, originalSampleRate) {
        if (originalSampleRate === this.sampleRate) {
            return audioData;
        }

        // Log first resampling
        if (!this.hasLoggedResampling) {
            this.log(`Resampling audio from ${originalSampleRate}Hz to ${this.sampleRate}Hz`, true);
            this.hasLoggedResampling = true;
        }

        // Simple linear resampling (for production, use a better algorithm)
        const ratio = this.sampleRate / originalSampleRate;
        const newLength = Math.round(audioData.length * ratio);
        const result = new Float32Array(newLength);

        for (let i = 0; i < newLength; i++) {
            const index = i / ratio;
            const indexFloor = Math.floor(index);
            const indexCeil = Math.min(indexFloor + 1, audioData.length - 1);
            const fraction = index - indexFloor;

            // Linear interpolation
            result[i] = audioData[indexFloor] * (1 - fraction) + audioData[indexCeil] * fraction;
        }

        return result;
    }

    /**
     * Convert Float32Array to 16-bit PCM Int16Array
     */
    floatTo16BitPCM(input) {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            // Convert float audio data [-1.0, 1.0] to 16-bit PCM [-32768, 32767]
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output;
    }

    /**
     * Convert ArrayBuffer to Base64 string
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }
}