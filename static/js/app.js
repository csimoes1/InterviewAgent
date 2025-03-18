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

    // Auto-scroll variables
    let isScrolledToBottom = true;
    let scrollObserver = null;

    // Event listeners
    startButton.addEventListener('click', startRecording);
    stopButton.addEventListener('click', stopRecording);
    resetButton.addEventListener('click', resetConversation);

    // Set up scroll detection
    setupScrollDetection();

    // Set up audio handler callbacks
    audioHandler.onStatusChange = updateStatus;
    audioHandler.onTranscription = handleTranscription;
    audioHandler.onAIResponse = handleAIResponse;
    audioHandler.onError = handleError;

    /**
     * Set up scroll position detection
     */
    function setupScrollDetection() {
        // Track whether user has scrolled away from bottom
        conversationElement.addEventListener('scroll', () => {
            const scrollPosition = conversationElement.scrollTop + conversationElement.clientHeight;
            const scrollHeight = conversationElement.scrollHeight;

            // Consider "close to bottom" if within 50px of bottom
            isScrolledToBottom = (scrollHeight - scrollPosition) < 50;
        });

        // Set up mutation observer to detect when content is added
        scrollObserver = new MutationObserver((mutations) => {
            // If user is scrolled to bottom, keep them at bottom when new content is added
            if (isScrolledToBottom) {
                scrollToBottom(true);
            }
        });

        // Start observing
        scrollObserver.observe(conversationElement, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    /**
     * Scroll conversation to bottom
     */
    function scrollToBottom(smooth = false) {
        // Use smooth scrolling animation when requested
        if (smooth) {
            conversationElement.scrollTo({
                top: conversationElement.scrollHeight,
                behavior: 'smooth'
            });
        } else {
            conversationElement.scrollTop = conversationElement.scrollHeight;
        }
    }

    /**
     * Start recording audio
     */
    async function startRecording() {
        // Only initialize and start after user interaction
        const initialized = await audioHandler.initialize();
        if (initialized) {
            await audioHandler.startRecording();
            // Update UI
            startButton.disabled = true;
            stopButton.disabled = false;
            listeningIndicator.classList.add('active');
        }
        // updateStatus('Initializing...');
        //
        // const started = await audioHandler.startRecording();
        //
        // if (started) {
        //     startButton.disabled = true;
        //     stopButton.disabled = false;
        //     listeningIndicator.classList.add('active');
        // }
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

        // Force scroll to bottom on reset
        scrollToBottom();
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

        // The MutationObserver will handle scrolling if user is at bottom
        // But we'll also force a scroll when a new message is added
        scrollToBottom(true);
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

            // Initial scroll to bottom
            scrollToBottom();
        } catch (error) {
            handleError(error.message);
        }
    }

    // Start initialization
    init();

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        // Clean up observer
        if (scrollObserver) {
            scrollObserver.disconnect();
        }

        audioHandler.close();
    });
});