import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from core.chat_models import CaseConversation
from config.settings import settings

logger = logging.getLogger(__name__)

class ChatStorage:
    def __init__(self):
        self.storage_dir = Path(settings.chat_storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_conversation(self, conversation: CaseConversation) -> None:
        try:
            file_path = self.storage_dir / f"{conversation.conversation_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved conversation {conversation.conversation_id}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save conversation: {e}", exc_info=True)
            raise

    def load_conversation(self, conversation_id: str) -> Optional[CaseConversation]:
        try:
            file_path = self.storage_dir / f"{conversation_id}.json"
            if not file_path.exists():
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return CaseConversation.from_dict(data)
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}", exc_info=True)
            return None

    def list_conversations(self) -> List[Dict[str, Any]]:
        conversations: List[Dict[str, Any]] = []
        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    conversations.append({
                        "conversation_id": data["conversation_id"],
                        "case_citation": data["case_citation"],
                        "created_at": data.get("created_at"),
                        "last_updated": data.get("last_updated"),
                        "message_count": len(data.get("messages", []))
                    })
                except (json.JSONDecodeError, KeyError, IOError, OSError) as e:
                    logger.error(f"Failed to read {file_path}: {e}")
        except OSError as e:
            logger.error(f"Failed to list conversations: {e}", exc_info=True)

        conversations.sort(key=lambda x: (x.get("last_updated") or ""), reverse=True)
        return conversations

    def list_conversations_for_case(self, file_path: str) -> List[Dict[str, Any]]:
        all_conversations = self.list_conversations()
        return [c for c in all_conversations if self._matches_case(c["conversation_id"], file_path)]

    def _matches_case(self, conversation_id: str, file_path: str) -> bool:
        conv = self.load_conversation(conversation_id)
        return conv is not None and conv.file_path == file_path

    def delete_conversation(self, conversation_id: str) -> None:
        try:
            file_path = self.storage_dir / f"{conversation_id}.json"
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation {conversation_id}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to delete conversation: {e}", exc_info=True)
            raise