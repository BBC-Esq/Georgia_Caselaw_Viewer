# core/chat_models.py
"""Data models for case chat conversations."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal

@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ChatMessage":
        return ChatMessage(
            role=d["role"],
            content=d["content"],
            timestamp=d.get("timestamp", datetime.now().isoformat())
        )

@dataclass
class CaseConversation:
    conversation_id: str
    case_citation: str
    file_path: str
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, role: Literal["user", "assistant"], content: str):
        self.messages.append(ChatMessage(role=role, content=content))
        self.last_updated = datetime.now().isoformat()

    def get_conversation_history(self) -> list[dict]:
        """Returns messages in OpenAI API format (excludes system message)."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
            if msg.role != "system"
        ]

    def to_dict(self):
        return {
            "conversation_id": self.conversation_id,
            "case_citation": self.case_citation,
            "file_path": self.file_path,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }

    @staticmethod
    def from_dict(d: dict) -> "CaseConversation":
        return CaseConversation(
            conversation_id=d["conversation_id"],
            case_citation=d["case_citation"],
            file_path=d["file_path"],
            messages=[ChatMessage.from_dict(m) for m in d.get("messages", [])],
            created_at=d.get("created_at", datetime.now().isoformat()),
            last_updated=d.get("last_updated", datetime.now().isoformat())
        )