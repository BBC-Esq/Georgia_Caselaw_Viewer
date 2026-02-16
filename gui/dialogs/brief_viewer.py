from pathlib import Path
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QScrollArea, QWidget, QFrame, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BriefViewer(QDialog):
    def __init__(self, parent: Optional[QDialog] = None, html_path: str = "", model_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Case Brief")
        self._html_path = html_path
        self._model_name = model_name or "AI"
        self._accumulated_text = ""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel("<b>Case Brief</b>")
        header.setObjectName("header")
        header.setWordWrap(True)
        layout.addWidget(header)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.container.setObjectName("darkContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(12)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setAlignment(Qt.AlignTop)
        from gui.widgets.chat_bubble import ChatBubble
        self.bubble = ChatBubble("assistant", "", custom_label=f"{self._model_name}:")
        self.bubble.setObjectName("assistant")
        self.bubble.setMaximumWidth(10000)
        self.container_layout.addWidget(self.bubble)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.StyledPanel)
        button_frame.setObjectName("footer")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(15, 12, 15, 12)
        button_layout.setSpacing(8)
        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.setProperty("class", "primary")
        self.export_pdf_btn.setEnabled(False)
        self.export_pdf_btn.clicked.connect(lambda: self._export_to_format("pdf"))
        self.export_docx_btn = QPushButton("Export to DOCX")
        self.export_docx_btn.setProperty("class", "primary")
        self.export_docx_btn.setEnabled(False)
        self.export_docx_btn.clicked.connect(lambda: self._export_to_format("docx"))
        self.export_txt_btn = QPushButton("Export to TXT")
        self.export_txt_btn.setProperty("class", "primary")
        self.export_txt_btn.setEnabled(False)
        self.export_txt_btn.clicked.connect(lambda: self._export_to_format("txt"))
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setProperty("class", "primary")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.close_btn = QPushButton("Close")
        self.close_btn.setProperty("class", "secondary")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.export_pdf_btn)
        button_layout.addWidget(self.export_docx_btn)
        button_layout.addWidget(self.export_txt_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        layout.addWidget(button_frame)
        self.resize(850, 750)

    def _copy_to_clipboard(self) -> None:
        if not self._accumulated_text.strip():
            return
        QApplication.clipboard().setText(self._accumulated_text)
        original = self.copy_btn.text()
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(original))

    def _export_to_format(self, fmt: str) -> None:
        if not self._accumulated_text.strip():
            QMessageBox.information(self, "Nothing to Export", "There is no brief content yet.")
            return
        
        filter_map = {"pdf": "PDF Files (*.pdf)", "docx": "Word Documents (*.docx)", "txt": "Text Files (*.txt)"}
        default_name = f"case_brief.{fmt}"
        if self._html_path:
            default_name = f"{Path(self._html_path).stem}_brief.{fmt}"
        path, _ = QFileDialog.getSaveFileName(self, f"Export Brief to {fmt.upper()}", default_name, filter_map[fmt])
        if not path:
            return
        if not path.lower().endswith(f".{fmt}"):
            path = f"{path}.{fmt}"
        try:
            from utils.helpers import save_brief
            save_brief(self._accumulated_text, Path(path), fmt)
            QMessageBox.information(self, "Exported", f"Brief exported to {path}")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Failed", str(e))

    def append_chunk(self, text: str) -> None:
        self._accumulated_text += text
        self.bubble.append_text(text)

    def finish(self) -> None:
        self.export_pdf_btn.setEnabled(True)
        self.export_docx_btn.setEnabled(True)
        self.export_txt_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)
