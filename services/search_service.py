from PySide6.QtCore import QObject, Signal, QTimer
import pandas as pd
from datetime import date
from time import perf_counter
from typing import Optional
import logging
from core.search import SearchEngine, SearchResult
from config.settings import settings
from utils.date_filter import filter_by_date_range

logger = logging.getLogger(__name__)


class SearchService(QObject):
    search_complete = Signal(SearchResult)
    search_started = Signal()

    def __init__(self):
        super().__init__()
        self._data = pd.DataFrame()
        self._engine = SearchEngine(
            fuzzy_threshold=settings.fuzzy_search_threshold,
            fuzzy_limit=settings.fuzzy_search_limit,
        )
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute_search)
        self._debounce_ms = settings.search_debounce_ms
        self._column = ""
        self._query = ""
        
        self._from_date: Optional[date] = None
        self._to_date: Optional[date] = None

    def set_data(self, data: pd.DataFrame):
        self._data = data
        self._engine.clear_cache()

    def set_date_filters(self, from_date: Optional[date], to_date: Optional[date]):
        self._from_date = from_date
        self._to_date = to_date
        
        if not self._data.empty and self._column:
            self._timer.stop()
            self._timer.start(self._debounce_ms)

    def schedule_search(self, column: str, query: str):
        self._column = column
        self._query = query
        self._timer.stop()
        self._timer.start(self._debounce_ms)

    def _execute_search(self):
        if self._data.empty or not self._column:
            return
            
        self.search_started.emit()
        start = perf_counter()
        
        search_data = self._data
        if self._from_date is not None or self._to_date is not None:
            search_data = filter_by_date_range(
                self._data,
                from_date=self._from_date,
                to_date=self._to_date,
            )
            logger.info(f"Date filtering: {len(self._data)} → {len(search_data)} rows")
        
        result = self._engine.search(
            search_data,
            self._column,
            self._query,
            min_query_length=settings.min_query_length_for_fuzzy,
            max_exact_before_fuzzy=settings.max_exact_matches_before_fuzzy,
        )
        result.duration = perf_counter() - start
        self.search_complete.emit(result)