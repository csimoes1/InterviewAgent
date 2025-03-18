/**
 * User Mapping Constants
 * Maps email addresses to user names
 */

const USERS = {
    // known users
    "csimoes1@gmail.com": "Chris Simoes",
    "mortenmo@gmail.com": "Morten Moeller",


    // Department managers
    "engineering@example.com": "David Rodriguez",
    "marketing@example.com": "Jennifer Smith",
    "sales@example.com": "Christopher Lee",
    "hr@example.com": "Emily Davis",

    // Team members
    "developer1@example.com": "Alex Thompson",
    "developer2@example.com": "Jessica Martinez",
    "designer@example.com": "Ryan Wilson",
    "analyst@example.com": "Olivia Taylor",

    // Add more users as needed
};

/**
 * Get user name from email
 * @param {string} email - The email address to look up
 * @returns {string|null} - The user name if found, or null if not found
 */
function getUserByEmail(email) {
    // Convert email to lowercase for case-insensitive comparison
    const normalizedEmail = email.toLowerCase().trim();

    // Check if email exists in our mapping
    if (USERS.hasOwnProperty(normalizedEmail)) {
        return USERS[normalizedEmail];
    }

    // If email doesn't match, check for domain matches
    // This allows for matching any address from certain domains
    const domain = normalizedEmail.split('@')[1];
    if (domain) {
        const domainMapping = {
            "partner.example.com": "Partner Representative",
            "client.example.com": "Client Contact",
            "vendor.example.com": "Vendor Representative"
        };

        if (domainMapping.hasOwnProperty(domain)) {
            return domainMapping[domain];
        }
    }

    // No match found
    return null;
}

/**
 * Extract the username portion from an email address
 * Returns all characters before the @ symbol
 *
 * @param {string} email - The email address to parse
 * @returns {string} - The username portion of the email
 */
function getUsernameFromEmail(email) {
    // Check if email is valid
    if (!email || typeof email !== 'string') {
        return '';
    }

    // Split the email address at the @ symbol
    const parts = email.split('@');

    // Return the first part (before the @ symbol)
    return parts[0] || '';
}