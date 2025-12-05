from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton, QLabel, QSizePolicy, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from typing import Optional

class ChatBubble(QFrame):
    def __init__(self, role: str, content: str = "", parent: Optional[QFrame] = None, custom_label: Optional[str] = None):
        super().__init__(parent)
        self.role = role
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        label_text = custom_label if custom_label else ("You:" if role == "user" else "Assistant:")
        role_label = QLabel(label_text)
        role_font = QFont()
        role_font.setBold(True)
        role_font.setPointSize(9)
        role_label.setFont(role_font)
        header_layout.addWidget(role_label)
        header_layout.addStretch()
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setMaximumWidth(60)
        self.copy_btn.setMaximumHeight(24)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setToolTip("Copy this message")
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        header_layout.addWidget(self.copy_btn)
        layout.addLayout(header_layout)
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.setFrameStyle(QFrame.NoFrame)
        self.content_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        if content:
            self.content_browser.setMarkdown(content)
        self.content_browser.document().documentLayout().documentSizeChanged.connect(lambda: self._sync_height())
        self._sync_height()
        layout.addWidget(self.content_browser)
        if role == "user":
            self.setMaximumWidth(600)
        else:
            self.setMaximumWidth(700)
        self._accumulated_text = content

    def _sync_height(self):
        doc_h = self.content_browser.document().size().height()
        h = int(doc_h + 20)
        self.content_browser.setMinimumHeight(h)
        self.content_browser.setMaximumHeight(h)

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self._accumulated_text)
        original_text = self.copy_btn.text()
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(original_text))

    def append_text(self, text: str) -> None:
        self._accumulated_text += text
        self.content_browser.setMarkdown(self._accumulated_text)
