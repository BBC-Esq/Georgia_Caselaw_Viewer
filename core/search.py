import pandas as pd
from dataclasses import dataclass
from thefuzz import process, fuzz
from typing import Dict, Tuple, List, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    exact_matches: pd.DataFrame
    fuzzy_matches: pd.DataFrame
    total_results: pd.DataFrame
    duration: float
    success: bool
    message: str = ""
    fuzzy_count: int = 0


class SearchEngine:
    def __init__(self, fuzzy_threshold: int = 72, fuzzy_limit: int = 15):
        self.fuzzy_threshold = fuzzy_threshold
        self.fuzzy_limit = fuzzy_limit
        self._string_columns_cache: Dict[Tuple[int, str], pd.Series] = {}
        self._unique_values_cache: Dict[Tuple[int, str], List[Any]] = {}

    def search(
        self,
        data: pd.DataFrame,
        column: str,
        query: str,
        min_query_length: int = 3,
        max_exact_before_fuzzy: int = 5,
    ) -> SearchResult:
        try:
            if column not in data.columns:
                raise ValueError(f"Column '{column}' not found in data")

            string_column = self._get_string_column(data, column)
            exact_matches = data[
                string_column.str.contains(query, na=False, case=False, regex=False)
            ]

            fuzzy_matches = pd.DataFrame()
            if (
                len(exact_matches) < max_exact_before_fuzzy
                and len(query) >= min_query_length
            ):
                fuzzy_matches = self._fuzzy_search(
                    data, string_column, query, exact_matches.index
                )

            total_results = pd.concat([exact_matches, fuzzy_matches]).drop_duplicates()

            return SearchResult(
                exact_matches=exact_matches,
                fuzzy_matches=fuzzy_matches,
                total_results=total_results,
                duration=0.0,
                success=True,
                message=f"Found {len(exact_matches)} exact matches",
                fuzzy_count=len(fuzzy_matches),
            )
        except ValueError as e:
            logger.error(f"Search validation failed: {e}", exc_info=True)
            return SearchResult(
                exact_matches=pd.DataFrame(),
                fuzzy_matches=pd.DataFrame(),
                total_results=pd.DataFrame(),
                duration=0.0,
                success=False,
                message=str(e),
            )
        except Exception as e:
            logger.error(f"Search failed unexpectedly: {e}", exc_info=True)
            return SearchResult(
                exact_matches=pd.DataFrame(),
                fuzzy_matches=pd.DataFrame(),
                total_results=pd.DataFrame(),
                duration=0.0,
                success=False,
                message=f"Unexpected error: {str(e)}",
            )

    def _get_string_column(self, data: pd.DataFrame, column: str) -> pd.Series:
        key = (id(data), column)
        if key not in self._string_columns_cache:
            self._string_columns_cache[key] = data[column].astype(str)
        return self._string_columns_cache[key]

    def _get_unique_values(self, data: pd.DataFrame, column: str) -> List[Any]:
        key = (id(data), column)
        if key not in self._unique_values_cache:
            self._unique_values_cache[key] = self._get_string_column(
                data, column
            ).unique().tolist()
        return self._unique_values_cache[key]

    def _fuzzy_search(self, data: pd.DataFrame, string_column: pd.Series, query: str, exclude_indices: pd.Index) -> pd.DataFrame:
        unique_values = self._get_unique_values(data, string_column.name)
        fuzzy_results = process.extractBests(
            query=query,
            choices=unique_values,
            scorer=fuzz.token_set_ratio,
            processor=lambda x: str(x).lower().strip(),
            score_cutoff=self.fuzzy_threshold,
            limit=self.fuzzy_limit,
        )

        value_to_indices: Dict[Any, List[int]] = {}
        for idx, val in string_column.items():
            if idx not in exclude_indices:
                value_to_indices.setdefault(val, []).append(idx)

        fuzzy_indices: List[int] = []
        for match, _ in fuzzy_results:
            fuzzy_indices.extend(value_to_indices.get(match, []))

        return data.iloc[fuzzy_indices] if fuzzy_indices else pd.DataFrame()

    def clear_cache(self) -> None:
        self._string_columns_cache.clear()
        self._unique_values_cache.clear()