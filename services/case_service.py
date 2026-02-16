from PySide6.QtCore import QObject, Signal
from typing import List
import logging
from data.workers.stream_worker import StreamWorker
from core.brief_utils import build_prompt, BriefRequest
from core.html_parser import parse_html_content
from config.settings import settings, requires_api_key

logger = logging.getLogger(__name__)

class CaseService(QObject):
    brief_chunk = Signal(str)
    brief_ready = Signal(str)
    error = Signal(str)
    api_key_missing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: List[StreamWorker] = []

    def copy_case_text(self, file_path: str) -> bool:
        from PySide6.QtWidgets import QApplication
        try:
            QApplication.clipboard().setText(parse_html_content(file_path))
            return True
        except Exception as e:
            logger.error(f"Copy case text failed: {e}", exc_info=True)
            return False

    def generate_case_brief(self, request: BriefRequest) -> None:
        try:
            if self._workers:
                logger.warning("Brief generation already in progress, ignoring request")
                return

            if requires_api_key(request.model) and not settings.has_openai_api_key():
                logger.warning("OpenAI API key not configured")
                self.api_key_missing.emit()
                return

            case_text = parse_html_content(request.file_path)
            prompt = build_prompt(request, case_text)

            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]

            worker = StreamWorker(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                verbosity=request.verbosity,
                reasoning_effort=settings.brief_reasoning_effort
            )

            worker.setParent(self)
            worker.chunk.connect(self.brief_chunk.emit)
            worker.done.connect(self.brief_ready.emit)
            worker.error.connect(self.error.emit)
            worker.finished.connect(lambda w=worker: self._cleanup(w))

            self._workers.append(worker)
            worker.start()
            
        except Exception as e:
            logger.error(f"Failed to start brief generation: {e}", exc_info=True)
            self.error.emit(str(e))

    def _cleanup(self, worker: StreamWorker) -> None:
        try:
            self._workers.remove(worker)
        except ValueError:
            pass
        worker.deleteLater()