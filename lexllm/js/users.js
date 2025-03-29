
/**
 * Get user name from email
 * @param {string} email - The email address to look up
 * @returns {string|null} - The user name if found, or null if not found
 */
async function getUserByEmail(email) {
    try {
        const response = await fetch(`/api/user?email=${encodeURIComponent(email)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user:', error);
        return null;
    }
}

