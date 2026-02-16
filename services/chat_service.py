from PySide6.QtCore import QObject, Signal
from typing import List, Dict, Any, Optional
import logging
import hashlib
from datetime import datetime
from core.chat_models import CaseConversation, ChatMessage
from core.html_parser import parse_html_content
from data.chat_storage import ChatStorage
from data.workers.stream_worker import StreamWorker
from config.settings import settings, requires_api_key

logger = logging.getLogger(__name__)

DEFAULT_CHAT_TEMPERATURE = 0.7

class ChatService(QObject):
    message_chunk = Signal(str)
    message_ready = Signal(str)
    error = Signal(str)
    api_key_missing = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._storage = ChatStorage()
        self._workers: List[StreamWorker] = []
        self._active_conversation: Optional[CaseConversation] = None

    def start_new_conversation(self, file_path: str, citation: str) -> Optional[CaseConversation]:
        try:
            if requires_api_key(settings.chat_model) and not settings.has_openai_api_key():
                logger.warning("OpenAI API key not configured for chat")
                self.api_key_missing.emit()
                return None

            case_text = parse_html_content(file_path)
            conversation_id = self._generate_conversation_id(file_path)

            conversation = CaseConversation(
                conversation_id=conversation_id,
                case_citation=citation,
                file_path=file_path
            )

            system_prompt = self._build_system_prompt(case_text, citation)
            conversation.messages.append(
                ChatMessage(role="system", content=system_prompt)
            )

            self._active_conversation = conversation
            self._storage.save_conversation(conversation)
            return conversation

        except Exception as e:
            logger.error(f"Failed to start conversation: {e}", exc_info=True)
            raise

    def load_conversation(self, conversation_id: str) -> Optional[CaseConversation]:
        conversation = self._storage.load_conversation(conversation_id)
        if conversation:
            self._active_conversation = conversation
        return conversation

    def send_message(self, user_message: str) -> None:
        if not self._active_conversation:
            raise RuntimeError("No active conversation")

        if requires_api_key(settings.chat_model) and not settings.has_openai_api_key():
            logger.warning("OpenAI API key not configured")
            self.api_key_missing.emit()
            return

        self._active_conversation.add_message("user", user_message)

        messages: List[Dict[str, str]] = []
        for msg in self._active_conversation.messages:
            messages.append({"role": msg.role, "content": msg.content})

        worker = StreamWorker(
            messages=messages,
            model=settings.chat_model,
            temperature=DEFAULT_CHAT_TEMPERATURE,
            verbosity=settings.chat_verbosity,
            reasoning_effort=settings.chat_reasoning_effort
        )

        worker.setParent(self)
        worker.chunk.connect(self.message_chunk.emit)
        worker.done.connect(self._on_message_complete)
        worker.error.connect(self._on_message_error)
        worker.finished.connect(lambda w=worker: self._cleanup(w))

        self._workers.append(worker)
        worker.start()

    def _on_message_complete(self, full_message: str) -> None:
        if self._active_conversation:
            self._active_conversation.add_message("assistant", full_message)
            self._storage.save_conversation(self._active_conversation)
            self.message_ready.emit(full_message)

    def _on_message_error(self, error_msg: str) -> None:
        if self._active_conversation and self._active_conversation.messages:
            last = self._active_conversation.messages[-1]
            if last.role == "user":
                self._active_conversation.messages.pop()
                logger.info("Rolled back user message after API error")
        self.error.emit(error_msg)

    def get_active_conversation(self) -> Optional[CaseConversation]:
        return self._active_conversation

    def list_all_conversations(self) -> List[Dict[str, Any]]:
        return self._storage.list_conversations()

    def list_conversations_for_case(self, file_path: str) -> List[Dict[str, Any]]:
        return self._storage.list_conversations_for_case(file_path)

    def delete_conversation(self, conversation_id: str) -> None:
        self._storage.delete_conversation(conversation_id)

    def _build_system_prompt(self, case_text: str, citation: str) -> str:
        return f"""You are a knowledgeable legal assistant helping a lawyer understand the following court case.

CASE: {citation}

FULL CASE TEXT:
{case_text}

Your role is to answer questions about this case accurately and helpfully. You should:
- Cite specific parts of the opinion when relevant
- Explain legal concepts clearly
- Point out important procedural details
- Identify key holdings and reasoning
- Note dissents or concurrences when asked
- Help the lawyer understand how this case might apply to their work

Be concise but thorough. If asked about something not in the case, say so clearly."""

    def _generate_conversation_id(self, file_path: str) -> str:
        timestamp = datetime.now().isoformat()
        unique_string = f"{file_path}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _cleanup(self, worker: StreamWorker) -> None:
        try:
            self._workers.remove(worker)
        except ValueError:
            pass
        worker.deleteLater()