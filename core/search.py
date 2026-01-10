import pandas as pd
from dataclasses import dataclass
from thefuzz import process, fuzz
from typing import Dict, Tuple, List, Any, Set, Optional
import logging

logger = logging.getLogger(__name__)

CHUNK_SIZE = 5000


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

        self._source_data_id: Optional[int] = None
        self._string_columns_cache: Dict[str, pd.Series] = {}
        self._unique_values_cache: Dict[str, List[Any]] = {}
        self._value_to_indices_cache: Dict[str, Dict[Any, List[int]]] = {}

    def set_source_data(self, data: pd.DataFrame) -> None:
        new_id = id(data)
        if self._source_data_id != new_id:
            self._source_data_id = new_id
            self.clear_cache()

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
        except MemoryError as e:
            logger.error(f"Search ran out of memory: {e}", exc_info=True)
            return SearchResult(
                exact_matches=pd.DataFrame(),
                fuzzy_matches=pd.DataFrame(),
                total_results=pd.DataFrame(),
                duration=0.0,
                success=False,
                message="Search ran out of memory. Try a more specific query.",
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
        if column in self._string_columns_cache:
            cached = self._string_columns_cache[column]
            return cached.loc[cached.index.intersection(data.index)]

        string_col = data[column].astype(str)
        self._string_columns_cache[column] = string_col
        return string_col

    def _get_unique_values(self, data: pd.DataFrame, column: str) -> List[Any]:
        string_col = self._get_string_column(data, column)
        return string_col.unique().tolist()

    def _get_value_to_indices(
        self, data: pd.DataFrame, string_column: pd.Series
    ) -> Dict[Any, List[int]]:
        column = string_column.name

        value_to_indices: Dict[Any, List[int]] = {}
        for idx, val in string_column.items():
            value_to_indices.setdefault(val, []).append(idx)
        return value_to_indices

    def _fuzzy_search(
        self,
        data: pd.DataFrame,
        string_column: pd.Series,
        query: str,
        exclude_indices: pd.Index,
    ) -> pd.DataFrame:
        unique_values = self._get_unique_values(data, string_column.name)
        
        logger.debug(f"Fuzzy search over {len(unique_values)} unique values")

        all_results: List[Tuple[Any, int]] = []

        for i in range(0, len(unique_values), CHUNK_SIZE):
            chunk = unique_values[i : i + CHUNK_SIZE]
            try:
                chunk_results = process.extractBests(
                    query=query,
                    choices=chunk,
                    scorer=fuzz.token_set_ratio,
                    processor=lambda x: str(x).lower().strip(),
                    score_cutoff=self.fuzzy_threshold,
                    limit=self.fuzzy_limit,
                )
                all_results.extend(chunk_results)
            except MemoryError:
                logger.warning(
                    f"Memory pressure during fuzzy search at chunk {i // CHUNK_SIZE + 1}, "
                    f"processed {i}/{len(unique_values)} values"
                )
                break

        all_results.sort(key=lambda x: x[1], reverse=True)
        top_results = all_results[: self.fuzzy_limit]

        value_to_indices = self._get_value_to_indices(data, string_column)

        exclude_set: Set[Any] = set(exclude_indices)

        fuzzy_indices: List[int] = []
        for match, _score in top_results:
            indices = value_to_indices.get(match, [])
            fuzzy_indices.extend(idx for idx in indices if idx not in exclude_set)

        return data.loc[fuzzy_indices] if fuzzy_indices else pd.DataFrame()

    def clear_cache(self) -> None:
        self._string_columns_cache.clear()
        self._unique_values_cache.clear()
        self._value_to_indices_cache.clear()
        logger.debug("Search engine cache cleared")