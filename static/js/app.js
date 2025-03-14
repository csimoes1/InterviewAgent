/**
 * Main Application Logic
 * Handles UI interaction and coordinates with the AudioHandler
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const resetButton = document.getElementById('reset-button');
    const statusElement = document.getElementById('status');
    const listeningIndicator = document.getElementById('listening-indicator');
    const conversationElement = document.getElementById('conversation');

    // Create audio handler
    const audioHandler = new AudioHandler();

    // Event listeners
    startButton.addEventListener('click', startRecording);
    stopButton.addEventListener('click', stopRecording);
    resetButton.addEventListener('click', resetConversation);

    // Set up audio handler callbacks
    audioHandler.onStatusChange = updateStatus;
    audioHandler.onTranscription = handleTranscription;
    audioHandler.onAIResponse = handleAIResponse;
    audioHandler.onError = handleError;

    /**
     * Start recording audio
     */
    async function startRecording() {
        updateStatus('Initializing...');

        const started = await audioHandler.startRecording();

        if (started) {
            startButton.disabled = true;
            stopButton.disabled = false;
            listeningIndicator.classList.add('active');
        }
    }

    /**
     * Stop recording audio
     */
    function stopRecording() {
        audioHandler.stopRecording();
        startButton.disabled = false;
        stopButton.disabled = true;
        listeningIndicator.classList.remove('active');
    }

    /**
     * Reset the conversation
     */
    function resetConversation() {
        // Clear conversation UI
        while (conversationElement.firstChild) {
            if (conversationElement.firstChild.classList.contains('system') &&
                conversationElement.childElementCount === 1) {
                // Keep the initial system message if it's the only one
                break;
            }
            conversationElement.removeChild(conversationElement.firstChild);
        }

        // Reset conversation in the backend
        audioHandler.resetConversation();

        // Add system message
        addMessage('system', 'Conversation has been reset.');
    }

    /**
     * Update status display
     */
    function updateStatus(status) {
        statusElement.textContent = status;
    }

    /**
     * Handle transcription from the server
     */
    function handleTranscription(text) {
        addMessage('user', text);
    }

    /**
     * Handle AI response from the server
     */
    function handleAIResponse(text) {
        addMessage('assistant', text);
    }

    /**
     * Handle errors
     */
    function handleError(error) {
        updateStatus(`Error: ${error}`);
        addMessage('system', `Error: ${error}`);
        stopRecording();
    }

    /**
     * Add a message to the conversation
     */
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.textContent = content;

        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        timeDiv.textContent = new Date().toLocaleTimeString();

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);

        conversationElement.appendChild(messageDiv);

        // Scroll to bottom
        conversationElement.scrollTop = conversationElement.scrollHeight;
    }

    /**
     * Initialize the application
     */
    async function init() {
        try {
            // Check for WebRTC support
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('WebRTC is not supported in this browser');
            }

            // Initialize audio (but don't start recording yet)
            await audioHandler.initialize();

            updateStatus('Ready to start');
        } catch (error) {
            handleError(error.message);
        }
    }

    // Start initialization
    init();

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        audioHandler.close();
    });
});