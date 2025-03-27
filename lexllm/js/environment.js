/**
 * Environment Configuration
 * Provides environment-specific configuration values
 */

(function() {
    // Determine if we're in production
    const isProduction = function() {
        return window.location.hostname === 'simoes.org' ||
            window.location.hostname === 'www.simoes.org';
    };

    // Get API base URL
    const getApiBaseUrl = function() {
        if (isProduction()) {
            return '/lexllm/api';
        } else {
            return '/api';  // Same in dev for relative paths
        }
    };

    // Get WebSocket URL
    const getWebSocketUrl = function() {
        if (isProduction()) {
            // Use secure WebSockets in production
            return `wss://${window.location.host}/ws/audio`;
        } else {
            // Use regular WebSockets in development
            return `ws://${window.location.host}/ws/audio`;
        }
    };

    // Debug information
    console.log(`Environment: ${isProduction() ? 'Production' : 'Development'}`);
    console.log(`API Base URL: ${getApiBaseUrl()}`);
    console.log(`WebSocket URL: ${getWebSocketUrl()}`);

    // Expose configuration globally
    window.appConfig = {
        isProduction: isProduction,
        getApiBaseUrl: getApiBaseUrl,
        getWebSocketUrl: getWebSocketUrl
    };
})();