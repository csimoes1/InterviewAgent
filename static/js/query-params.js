/**
 * Query Parameter Handler
 * Extracts the name parameter from URL and updates the page title
 */

function updateTitleFromQueryParams() {
    // Get query parameters from the URL
    const urlParams = new URLSearchParams(window.location.search);
    const name = urlParams.get('name');

    // Update title and header if name parameter exists
    if (name) {
        // Update the page title
        document.title = `An Interview with ${name}`;

        // Also update the H1 header on the page
        const headerElement = document.querySelector('header h1');
        if (headerElement) {
            headerElement.textContent = `An Interview with ${name}`;
        }

        // Update the initial system message if it exists
        const initialMessage = document.querySelector('.message.system .message-content');
        if (initialMessage) {
            initialMessage.textContent = `Hello ${name}! I'm ready to chat. Click the microphone button and start speaking.`;
        }
    }
}

// Execute when DOM is loaded
document.addEventListener('DOMContentLoaded', updateTitleFromQueryParams);