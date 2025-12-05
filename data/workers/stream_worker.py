from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_TEMPERATURE = 0.7
DEFAULT_VERBOSITY = "medium"
LMSTUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
LMSTUDIO_API_KEY = "lm-studio"

def _is_lmstudio(model: str) -> bool:
    m = (model or "").strip().lower()
    return m.startswith("lmstudio")

class StreamWorker(QThread):
    chunk = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, messages: List[Dict[str, str]], model: str, **kw: Any):
        super().__init__()
        self._messages = messages
        self._model = model
        self._kw = kw

    def run(self) -> None:
        full: List[str] = []
        try:
            client = self._get_client()

            for chunk_text in self._stream_response(client):
                if chunk_text:
                    self.chunk.emit(chunk_text)
                    full.append(chunk_text)

            self.done.emit("".join(full))
        except Exception as e:
            logger.error("Streaming failed", exc_info=True)
            self.error.emit(str(e))

    def _get_client(self):
        from openai import OpenAI
        from config.settings import settings

        if _is_lmstudio(self._model):
            return OpenAI(base_url=LMSTUDIO_BASE_URL, api_key=LMSTUDIO_API_KEY)
        return OpenAI(api_key=settings.openai_api_key)

    def _stream_response(self, client):
        if _is_lmstudio(self._model):
            yield from self._stream_lmstudio(client)
        else:
            yield from self._stream_openai(client)

    def _stream_lmstudio(self, client):
        stream = client.chat.completions.create(
            model=self._model,
            messages=self._messages,
            stream=True,
            temperature=self._kw.get("temperature", DEFAULT_TEMPERATURE),
        )
        in_think = False
        for ch in stream:
            delta = getattr(ch.choices[0].delta, "content", None)
            if delta is None:
                continue
            low = delta.lower()
            in_think = in_think or ("<think>" in low)
            if not in_think:
                yield delta
            if "</think>" in low:
                in_think = False

    def _stream_openai(self, client):
        args: Dict[str, Any] = {
            "model": self._model,
            "input": self._messages,
            "stream": True,
        }

        if self._model.startswith(("gpt-4.1", "gpt-4o")):
            args["temperature"] = self._kw.get("temperature", DEFAULT_TEMPERATURE)
        elif self._model == "gpt-5.1":
            args["text"] = {"verbosity": self._kw.get("verbosity", DEFAULT_VERBOSITY)}

        stream = client.responses.create(**args)

        for ev in stream:
            if ev.type == "response.output_text.delta":
                delta = ev.delta or ""
                if delta:
                    yield delta
            elif ev.type == "response.error":
                msg = str(getattr(ev, "error", "unknown error"))
                logger.error(f"OpenAI API error: {msg}")
                raise RuntimeError(msg)