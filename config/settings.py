from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
import tempfile
from typing import Tuple

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREFS_FILE = PROJECT_ROOT / "config" / "caselaw_viewer.json"
DEFAULT_BRIEFS_SAVE_DIR = PROJECT_ROOT / "CaseBriefs"
CHAT_STORAGE_DIR = PROJECT_ROOT / "CaseLawChats"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "DATABASE_updated_dates_added_enriched_FINAL_updated_may_2025.xlsx"

AVAILABLE_OPENAI_MODELS = [
    "gpt-5.2",
    "gpt-5.2-chat-latest",
    "gpt-5.1",
    "gpt-4.1",
    "gpt-4o",
]

MODEL_DISPLAY_NAMES = {
    "gpt-5.2": "gpt-5.2 (Thinking)",
    "gpt-5.2-chat-latest": "gpt-5.2 (Instant)",
    "gpt-5.1": "gpt-5.1",
    "gpt-4.1": "gpt-4.1",
    "gpt-4o": "gpt-4o",
    "lmstudio-local": "LM Studio (Local)",
}

def get_display_name(model: str) -> str:
    return MODEL_DISPLAY_NAMES.get(model, model)

def get_model_from_display_name(display_name: str) -> str:
    for model, name in MODEL_DISPLAY_NAMES.items():
        if name == display_name:
            return model
    return display_name

MODEL_PRICING = {
    "gpt-5.2": (1.75, 14.00),
    "gpt-5.2-chat-latest": (1.75, 14.00),
    "gpt-5.1": (1.25, 10.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4o": (2.50, 10.00),
    "lmstudio-local": (0.00, 0.00),
}

def get_model_pricing(model_name: str) -> tuple[float, float]:
    return MODEL_PRICING.get(model_name, (0.00, 0.00))

LOCAL_CHAT_MODELS = ["lmstudio-local"]
AVAILABLE_BRIEF_MODELS = AVAILABLE_OPENAI_MODELS + LOCAL_CHAT_MODELS

REASONING_EFFORT_OPTIONS = ["none", "low", "medium", "high", "xhigh"]

EXPECTED_COLUMNS = [
    "reporter_citation",
    "citation", 
    "case_name",
    "file_path",
    "date",
]

COLUMN_ALIASES = {
    "reporter_citation": ["reporter_citation", "reporter cite", "reporter", "reporter_cite"],
    "citation": ["citation", "full_citation", "case_citation", "cite"],
    "case_name": ["case_name", "case name", "style", "caption"],
    "file_path": ["file_path", "file path", "filepath", "html_path", "path"],
    "date": ["date", "decision_date", "case_date"],
}

def expected_columns() -> list:
    return list(EXPECTED_COLUMNS)

@dataclass
class WindowDefaults:
    X: int = 100
    Y: int = 100
    WIDTH: int = 1000
    HEIGHT: int = 700
    COLUMN_WIDTH_FILE_SELECTOR: int = 200

@dataclass
class SearchDefaults:
    DEBOUNCE_MS: int = 600
    FUZZY_THRESHOLD: int = 72
    FUZZY_LIMIT: int = 15
    MIN_QUERY_LENGTH_FOR_FUZZY: int = 3
    MAX_EXACT_MATCHES_BEFORE_FUZZY: int = 5

DEFAULT_MODEL = "gpt-5.2"
DEFAULT_EXPORT_FMT = "viewer"
DEFAULT_BRIEF_VERBOSITY = "low"
DEFAULT_BRIEF_REASONING_EFFORT = "medium"
DEFAULT_CHAT_VERBOSITY = "low"
DEFAULT_CHAT_REASONING_EFFORT = "medium"
DEFAULT_CHAT_MODEL = "gpt-5.2"
MAX_CHAT_HISTORY = 50
MAX_STATUS_MESSAGES = 4

WINDOW = WindowDefaults()
SEARCH = SearchDefaults()

def requires_api_key(model_name: str) -> bool:
    m = (model_name or "").strip().lower()
    return not m.startswith("lmstudio")

def supports_reasoning_effort(model_name: str) -> bool:
    return model_name == "gpt-5.2"

@dataclass
class Settings:
    database_path: str = str(DEFAULT_DATABASE_PATH)
    search_debounce_ms: int = SEARCH.DEBOUNCE_MS
    fuzzy_search_threshold: int = SEARCH.FUZZY_THRESHOLD
    fuzzy_search_limit: int = SEARCH.FUZZY_LIMIT
    min_query_length_for_fuzzy: int = SEARCH.MIN_QUERY_LENGTH_FOR_FUZZY
    max_exact_matches_before_fuzzy: int = SEARCH.MAX_EXACT_MATCHES_BEFORE_FUZZY
    max_status_messages: int = MAX_STATUS_MESSAGES
    window_title: str = "Chintella Law Case Search"
    window_geometry: Tuple[int, int, int, int] = (WINDOW.X, WINDOW.Y, WINDOW.WIDTH, WINDOW.HEIGHT)
    column_width_file_selector: int = WINDOW.COLUMN_WIDTH_FILE_SELECTOR
    model: str = field(default=DEFAULT_MODEL)
    export_fmt: str = field(default=DEFAULT_EXPORT_FMT)
    openai_api_key: str = field(default="")
    briefs_save_dir: str = field(default=str(DEFAULT_BRIEFS_SAVE_DIR))
    brief_verbosity: str = field(default=DEFAULT_BRIEF_VERBOSITY)
    brief_reasoning_effort: str = field(default=DEFAULT_BRIEF_REASONING_EFFORT)
    chat_model: str = field(default=DEFAULT_CHAT_MODEL)
    chat_verbosity: str = field(default=DEFAULT_CHAT_VERBOSITY)
    chat_reasoning_effort: str = field(default=DEFAULT_CHAT_REASONING_EFFORT)
    chat_storage_dir: str = field(default=str(CHAT_STORAGE_DIR))
    date_filter_from_enabled: bool = field(default=False)
    date_filter_from_date: str = field(default="")
    date_filter_to_enabled: bool = field(default=False)
    date_filter_to_date: str = field(default="")

    def save_user_prefs(self) -> bool:
        try:
            PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)

            database_relative = self._path_to_relative(self.database_path)

            data = {
                "model": self.model,
                "export_fmt": self.export_fmt,
                "briefs_save_dir": self.briefs_save_dir,
                "brief_verbosity": self.brief_verbosity,
                "brief_reasoning_effort": self.brief_reasoning_effort,
                "chat_model": self.chat_model,
                "chat_verbosity": self.chat_verbosity,
                "chat_reasoning_effort": self.chat_reasoning_effort,
                "chat_storage_dir": self.chat_storage_dir,
                "openai_api_key": self.openai_api_key,
                "date_filter_from_enabled": self.date_filter_from_enabled,
                "date_filter_from_date": self.date_filter_from_date,
                "date_filter_to_enabled": self.date_filter_to_enabled,
                "date_filter_to_date": self.date_filter_to_date,
                "database_path_relative": database_relative,
            }

            fd, tmp_path = tempfile.mkstemp(
                dir=str(PREFS_FILE.parent), suffix=".tmp"
            )
            try:
                with open(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                Path(tmp_path).replace(PREFS_FILE)
            except BaseException:
                Path(tmp_path).unlink(missing_ok=True)
                raise

            logger.info(f"User preferences saved successfully to {PREFS_FILE}")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Failed to save user preferences: {e}", exc_info=True)
            return False

    def load_user_prefs(self) -> None:
        if not PREFS_FILE.exists():
            logger.info(f"No preferences file found at {PREFS_FILE}, using defaults")
            return

        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.model = data.get("model", self.model)
            self.export_fmt = data.get("export_fmt", self.export_fmt)
            self.brief_verbosity = data.get("brief_verbosity", data.get("gpt5_verbosity", self.brief_verbosity))
            self.brief_reasoning_effort = data.get("brief_reasoning_effort", self.brief_reasoning_effort)
            self.chat_model = data.get("chat_model", self.chat_model)
            self.chat_verbosity = data.get("chat_verbosity", self.chat_verbosity)
            self.chat_reasoning_effort = data.get("chat_reasoning_effort", self.chat_reasoning_effort)
            self.openai_api_key = data.get("openai_api_key", self.openai_api_key)
            self.date_filter_from_enabled = data.get("date_filter_from_enabled", self.date_filter_from_enabled)
            self.date_filter_from_date = data.get("date_filter_from_date", self.date_filter_from_date)
            self.date_filter_to_enabled = data.get("date_filter_to_enabled", self.date_filter_to_enabled)
            self.date_filter_to_date = data.get("date_filter_to_date", self.date_filter_to_date)

            self.briefs_save_dir = self._validate_directory_path(
                data.get("briefs_save_dir", self.briefs_save_dir),
                DEFAULT_BRIEFS_SAVE_DIR,
                "briefs_save_dir"
            )

            self.chat_storage_dir = self._validate_directory_path(
                data.get("chat_storage_dir", self.chat_storage_dir),
                CHAT_STORAGE_DIR,
                "chat_storage_dir"
            )

            self.database_path = self._validate_database_path(data)
            
            logger.info("User preferences loaded successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in preferences file: {e}. Using defaults.", exc_info=True)
        except (IOError, OSError) as e:
            logger.error(f"Failed to load user preferences: {e}. Using defaults.", exc_info=True)

    def _validate_database_path(self, data: dict) -> str:

        if "database_path_relative" in data:
            relative_path = data["database_path_relative"]
            if relative_path:
                try:
                    resolved = self._relative_to_path(relative_path)
                    if resolved.exists():
                        logger.info(f"Using database from relative path: {resolved}")
                        return str(resolved)
                except Exception as e:
                    logger.warning(f"Could not resolve relative database path: {e}")

        if "database_path" in data:
            old_path = Path(data["database_path"])
            if old_path.exists():
                logger.info(f"Using database from absolute path: {old_path}")
                return str(old_path)
            else:
                logger.warning(f"Saved database path no longer exists: {old_path}")
                fallback = PROJECT_ROOT / old_path.name
                if fallback.exists():
                    logger.info(f"Found database in project root: {fallback}")
                    return str(fallback)

        if DEFAULT_DATABASE_PATH.exists():
            logger.info(f"Using default database path: {DEFAULT_DATABASE_PATH}")
            return str(DEFAULT_DATABASE_PATH)

        logger.warning(f"Database file not found, using default path anyway: {DEFAULT_DATABASE_PATH}")
        return str(DEFAULT_DATABASE_PATH)

    def _path_to_relative(self, path_str: str) -> str:
        try:
            path = Path(path_str).resolve()
            relative = path.relative_to(PROJECT_ROOT)
            return str(relative)
        except (ValueError, Exception):
            return Path(path_str).name

    def _relative_to_path(self, relative_str: str) -> Path:
        return (PROJECT_ROOT / relative_str).resolve()

    def _validate_directory_path(self, loaded_path: str, default_path: Path, name: str) -> str:
        try:
            path = Path(loaded_path)

            if self._is_likely_portable(path):
                path.mkdir(parents=True, exist_ok=True)

                if path.is_dir() and self._test_write_access(path):
                    logger.info(f"Using {name}: {path}")
                    return str(path)
                else:
                    logger.warning(f"Path exists but is not writable: {path}")
            else:
                logger.warning(
                    f"Loaded {name} '{loaded_path}' appears to be from a different computer. "
                    f"Using project-relative default instead."
                )

        except (OSError, PermissionError, ValueError) as e:
            logger.warning(
                f"Cannot use {name} '{loaded_path}': {e}. "
                f"This may be from a different computer. Falling back to default."
            )

        try:
            default_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using default {name}: {default_path}")
            return str(default_path)
        except Exception as e:
            logger.error(f"Could not create default {name} directory: {e}", exc_info=True)
            return str(default_path)

    def _is_likely_portable(self, path: Path) -> bool:
        try:
            if not path.is_absolute():
                return True

            try:
                path.relative_to(PROJECT_ROOT)
                return True
            except ValueError:
                pass

            if path.exists():
                return True

            parts = path.parts
            if len(parts) > 0:
                root = Path(parts[0])
                if root.exists():
                    return True
            
            return False
            
        except Exception:
            return False

    def _test_write_access(self, path: Path) -> bool:
        try:
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False

    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())

settings = Settings()
settings.load_user_prefs()