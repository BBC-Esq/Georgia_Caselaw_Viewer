from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QPushButton, QLabel, QScrollArea, QWidget, QFrame, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QTimer
from typing import Optional
import logging
from services.chat_service import ChatService
from core.chat_models import CaseConversation
from gui.widgets.chat_bubble import ChatBubble

logger = logging.getLogger(__name__)

class CaseChatDialog(QDialog):
    def __init__(self, parent: Optional[QDialog] = None, file_path: str = "", citation: str = "", conversation_id: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Chat: {citation}")
        self.resize(900, 700)
        self._file_path = file_path
        self._citation = citation
        self._chat_service = ChatService()
        self._current_assistant_bubble = None
        self._setup_ui()
        self._connect_signals()
        if conversation_id:
            self._load_existing_conversation(conversation_id)
        else:
            self._start_new_conversation()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel(f"<b>Case:</b> {self._citation}")
        header.setObjectName("header")
        header.setWordWrap(True)
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setObjectName("darkContainer")

        self.chat_container = QWidget()
        self.chat_container.setObjectName("darkContainer")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.chat_container)
        layout.addWidget(self.scroll)

        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.StyledPanel)
        input_frame.setObjectName("inputFrame")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 12, 15, 12)
        input_layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask a question about this case...")
        self.input_box.setObjectName("chatInput")
        self.input_box.returnPressed.connect(self._send_message)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.send_btn = QPushButton("Send")
        self.send_btn.setProperty("class", "primary")
        self.send_btn.clicked.connect(self._send_message)

        self.clear_btn = QPushButton("New Conversation")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.clicked.connect(self._confirm_new_conversation)

        self.save_btn = QPushButton("Save")
        self.save_btn.setProperty("class", "secondary")
        self.save_btn.clicked.connect(self._save_conversation_to_file)

        self.close_btn = QPushButton("Close")
        self.close_btn.setProperty("class", "secondary")
        self.close_btn.clicked.connect(self.close)

        self.send_btn.setAutoDefault(True)
        self.send_btn.setDefault(True)
        self.clear_btn.setAutoDefault(False)
        self.save_btn.setAutoDefault(False)
        self.close_btn.setAutoDefault(False)

        button_row.addWidget(self.send_btn)
        button_row.addWidget(self.clear_btn)
        button_row.addWidget(self.save_btn)
        button_row.addStretch()
        button_row.addWidget(self.close_btn)

        input_layout.addWidget(self.input_box)
        input_layout.addLayout(button_row)
        layout.addWidget(input_frame)

    def _connect_signals(self) -> None:
        self._chat_service.message_chunk.connect(self._on_message_chunk)
        self._chat_service.message_ready.connect(self._on_message_complete)
        self._chat_service.error.connect(self._on_error)
        self._chat_service.api_key_missing.connect(self._on_api_key_missing)

    def _send_message(self) -> None:
        message = self.input_box.text().strip()
        if not message:
            return
        self.input_box.clear()
        self.send_btn.setDefault(False)
        self.input_box.setEnabled(False)
        self.send_btn.setEnabled(False)
        self._add_bubble("user", message)
        self._current_assistant_bubble = ChatBubble("assistant", "")
        self._current_assistant_bubble.setObjectName("assistant")
        self._add_widget_to_chat(self._current_assistant_bubble, align_right=False)
        try:
            self._chat_service.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to send message: {e}")
            self.input_box.setEnabled(True)
            self.send_btn.setEnabled(True)

    def _start_new_conversation(self) -> None:
        try:
            conversation = self._chat_service.start_new_conversation(self._file_path, self._citation)
            if conversation:
                self._add_system_message("Conversation started. Ask me anything about this case!")
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to start conversation: {e}")

    def _load_existing_conversation(self, conversation_id: str) -> None:
        try:
            conversation = self._chat_service.load_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            for msg in conversation.messages:
                if msg.role == "system":
                    continue
                self._add_bubble(msg.role, msg.content)
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load conversation: {e}")

    def _add_bubble(self, role: str, content: str) -> None:
        bubble = ChatBubble(role, content)
        bubble.setObjectName("user" if role == "user" else "assistant")
        align_right = role == "user"
        self._add_widget_to_chat(bubble, align_right)
        self._scroll_to_bottom()

    def _add_widget_to_chat(self, widget, align_right: bool = False) -> None:
        container = QHBoxLayout()
        if align_right:
            container.addStretch()
            container.addWidget(widget)
        else:
            container.addWidget(widget)
            container.addStretch()
        self.chat_layout.addLayout(container)

    def _add_system_message(self, text: str) -> None:
        label = QLabel(f"<i>{text}</i>")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setProperty("class", "systemNote")
        self.chat_layout.addWidget(label)

    def _on_message_chunk(self, chunk: str) -> None:
        if self._current_assistant_bubble:
            self._current_assistant_bubble.append_text(chunk)
            QTimer.singleShot(50, self._scroll_to_bottom)

    def _on_message_complete(self, full_message: str) -> None:
        self._current_assistant_bubble = None
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setDefault(True)
        self.input_box.setFocus()
        self._scroll_to_bottom()

    def _on_error(self, error_msg: str) -> None:
        if self._current_assistant_bubble:
            self._current_assistant_bubble.append_text("\n\n[Error: response failed]")
            self._current_assistant_bubble = None
        QMessageBox.critical(self, "Error", f"Chat error: {error_msg}")
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setDefault(True)

    def _on_api_key_missing(self) -> None:
        reply = QMessageBox.warning(
            self,
            "OpenAI API Key Required",
            "You need to configure your OpenAI API key to use this feature.\n\nWould you like to open Settings to add your API key?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            from gui.dialogs.settings_dialog import SettingsDialog
            SettingsDialog(self).exec()
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setDefault(True)
        self.input_box.setFocus()


    def _scroll_to_bottom(self) -> None:
        scrollbar = self.scroll.verticalScrollBar()
        QTimer.singleShot(100, lambda: scrollbar.setValue(scrollbar.maximum()))

    def _confirm_new_conversation(self) -> None:
        reply = QMessageBox.question(self, "New Conversation", "Start a new conversation about this case?\n\nCurrent conversation will be saved automatically.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            while self.chat_layout.count() > 0:
                item = self.chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())
            self._start_new_conversation()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _save_conversation_to_file(self) -> None:
        conversation = self._chat_service.get_active_conversation()
        if not conversation or len(conversation.messages) <= 1:
            QMessageBox.information(self, "No Messages", "No conversation to save yet.")
            return
        import re
        safe_cite = re.sub(r'[<>:"/\\|?*]', '-', self._citation).replace(' ', '_')
        filename = f"{safe_cite}_chat.txt"
        path, _ = QFileDialog.getSaveFileName(self, "Save Conversation", filename, "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"Case Chat: {self._citation}\n")
                    f.write(f"Date: {conversation.created_at}\n")
                    f.write("=" * 80 + "\n\n")
                    for msg in conversation.messages:
                        if msg.role == "system":
                            continue
                        role_header = "YOU:" if msg.role == "user" else "ASSISTANT:"
                        f.write(f"{role_header}\n{msg.content}\n\n" + "-" * 80 + "\n\n")
                QMessageBox.information(self, "Saved", f"Conversation saved to {path}")
            except Exception as e:
                logger.error(f"Failed to save conversation: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")
