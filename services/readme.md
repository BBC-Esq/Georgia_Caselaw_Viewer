# Services

- **case_service.py** — Orchestrates case brief generation by coordinating HTML parsing, prompt building, and streaming API calls with Qt signals.
- **chat_service.py** — Manages interactive case chat sessions including conversation lifecycle, message streaming, and persistent storage.
- **search_service.py** — Provides debounced search execution with date range filtering, connecting the search engine to the UI via Qt signals.
