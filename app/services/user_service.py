# app/services/user_service.py
from typing import Optional

USERS = {
    "csimoes1@gmail.com": "Chris Simoes",
    "mortenmo@gmail.com": "Morten Moeller",
    "mike.betzer@hypergiant.com": "Mike Betzer",
    "ljordan@gmail.com": "Leslie Jordan",
    "msimoes1325@gmail.com": "Mark Simoes",
    "heero@sprintmail.com": "Greg Simoes",
    "kjhayden@gmail.com": "Kenneth Hayden",
    "engineering@example.com": "David Rodriguez",
    "marketing@example.com": "Jennifer Smith",
    "sales@example.com": "Christopher Lee",
    "hr@example.com": "Emily Davis",
    "developer1@example.com": "Alex Thompson",
    "developer2@example.com": "Jessica Martinez",
    "designer@example.com": "Ryan Wilson",
    "analyst@example.com": "Olivia Taylor",
}

DOMAIN_MAPPING = {
    "partner.example.com": "Partner Representative",
    "client.example.com": "Client Contact",
    "vendor.example.com": "Vendor Representative"
}

def get_user_by_email(email: str) -> str|None:
    normalized_email = email.lower().strip()
    if normalized_email in USERS:
        return USERS[normalized_email]

    domain = normalized_email.split('@')[1]
    if domain in DOMAIN_MAPPING:
        return DOMAIN_MAPPING[domain]

    return None