from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid

class Message(BaseModel):
    """
    Represents a single message in a conversation.
    """
    id: str = None
    role: str  # "system", "user", or "assistant"
    content: str
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()

class Conversation(BaseModel):
    """
    Represents a conversation with message history.
    """
    id: str = None
    messages: List[Message] = []
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict = {}

    def __init__(self, **data):
        super().__init__(**data)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def add_message(self, role: str, content: str) -> Message:
        """
        Add a new message to the conversation.

        Args:
            role: The role of the sender ("system", "user", or "assistant")
            content: The message content

        Returns:
            The newly created message
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def to_dict(self) -> Dict:
        """
        Convert the conversation to a dictionary.

        Returns:
            Dictionary representation of the conversation
        """
        return {
            "id": self.id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in self.messages
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    def to_api_messages(self) -> List[Dict]:
        """
        Convert the conversation messages to a format suitable for the API.

        Returns:
            List of message dictionaries formatted for the API
        """
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in self.messages
        ]