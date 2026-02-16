import urllib.parse
import re
import os
from pathlib import Path
import yaml
import logging
from typing import Literal, List, Dict
import pandas as pd

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"http[s]?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F]{2}))+")

def is_url(text): 
    return bool(URL_PATTERN.match(str(text)))

def is_file_path(text): 
    return os.path.exists(str(text))

def is_local_html_file(text): 
    return isinstance(text, str) and text.lower().endswith(".html")

def convert_file_url_to_windows_path(file_url: str) -> str:
    if not file_url.lower().startswith("file://"):
        return file_url
    
    rest = urllib.parse.unquote(file_url[7:])
    
    rest = rest.lstrip("/")
    
    if len(rest) >= 2 and rest[1] == ":":
        return rest.replace("/", "\\")
    
    return f"\\\\{rest.replace('/', '\\')}"

def validate_and_resolve_path(file_path: str, fallback_subdir: str = "") -> Path:
    path = Path(file_path)
    if path.exists():
        return path
    
    base_dir = Path(__file__).resolve().parent.parent
    if fallback_subdir:
        fallback = base_dir / fallback_subdir / path.name
    else:
        fallback = base_dir / path.name
    
    if fallback.exists():
        return fallback
    
    raise FileNotFoundError(
        f"File not found at '{file_path}' or '{fallback}'"
    )

def load_yaml(path: Path, default=None):
    if not path.exists():
        return default or {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or default or {}
    except (yaml.YAMLError, IOError, OSError) as e:
        logger.error(f"Failed reading YAML '{path}': {e}", exc_info=True)
        return default or {}

def save_yaml(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    except (yaml.YAMLError, IOError, OSError) as e:
        logger.error(f"Failed saving YAML '{path}': {e}", exc_info=True)
        raise

def save_brief(text: str, filepath: Path, fmt: Literal["txt", "docx", "pdf"]) -> Path:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "txt":
        filepath.write_text(text, encoding="utf-8")
    elif fmt == "docx":
        _save_as_docx(text, filepath)
    elif fmt == "pdf":
        _save_as_pdf(text, filepath)
    else:
        raise ValueError(f"Unknown format '{fmt}'")
    return filepath

def _save_as_docx(text: str, filepath: Path) -> None:
    try:
        import docx
        from docx.shared import Pt
    except ImportError:
        raise RuntimeError("python-docx not installed")
    try:
        doc = docx.Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.space_before = Pt(0)
        for line in text.splitlines():
            doc.add_paragraph(line)
        doc.save(filepath)
    except Exception as e:
        logger.error(f"Failed to save DOCX: {e}", exc_info=True)
        raise

def _save_as_pdf(text: str, filepath: Path) -> None:
    try:
        import fitz
    except ImportError:
        raise RuntimeError("PyMuPDF not installed (pip install pymupdf)")

    try:
        doc = fitz.open()
        page = doc.new_page()
        y_pos = 72
        max_width = page.rect.width - 144

        def wrap_line(line: str) -> List[str]:
            if not line.strip():
                return [""]
            words = [w for w in line.split(" ") if w]
            if not words:
                return [""]
            wrapped: List[str] = []
            current = words[0]
            for word in words[1:]:
                test = f"{current} {word}"
                if fitz.get_text_length(test, fontsize=11) <= max_width:
                    current = test
                else:
                    wrapped.append(current)
                    current = word
            wrapped.append(current)
            return wrapped

        for raw_line in text.splitlines() or [""]:
            for segment in wrap_line(raw_line):
                page.insert_text((72, y_pos), segment, fontsize=11)
                y_pos += 15
                if y_pos > page.rect.height - 72:
                    page = doc.new_page()
                    y_pos = 72
        doc.save(filepath)
        doc.close()
    except Exception as e:
        logger.error(f"Failed to save PDF: {e}", exc_info=True)
        raise

def _canonicalize(label: str) -> str:

    return str(label).strip().lower().replace("-", "_").replace(" ", "_")


def build_alias_lut() -> Dict[str, str]:

    from config.settings import COLUMN_ALIASES
    
    lut: Dict[str, str] = {}
    for canonical, variants in COLUMN_ALIASES.items():
        for v in variants:
            lut[_canonicalize(v)] = canonical
    return lut


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    from config.settings import EXPECTED_COLUMNS
    
    lut = build_alias_lut()
    data = df.copy()
    
    rename_map: Dict[str, str] = {}
    for col in data.columns:
        norm = _canonicalize(col)
        if norm in lut:
            rename_map[col] = lut[norm]
        else:
            rename_map[col] = norm
    
    data = data.rename(columns=rename_map)
    
    if all(col in data.columns for col in ['year', 'month', 'day']):
        try:
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12,
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            
            month_nums = data['month'].astype(str).str.lower().map(month_map)
            data['month'] = pd.to_numeric(month_nums, errors='coerce').astype('Int64')
            data['year'] = pd.to_numeric(data['year'], errors='coerce').astype('Int64')
            data['day'] = pd.to_numeric(data['day'], errors='coerce').astype('Int64')
            
            data['date'] = _format_partial_date(data)
            
            logger.info("Created 'date' display column from year/month/day components")
        except Exception as e:
            logger.warning(f"Could not process date columns: {e}")
    
    for col in EXPECTED_COLUMNS:
        if col not in data.columns:
            data[col] = pd.NA
            logger.info(f"Added missing column '{col}' with NA values")

    front = [c for c in EXPECTED_COLUMNS if c in data.columns]
    date_cols = [c for c in ['year', 'month', 'day'] if c in data.columns]  # NEW
    extras = [c for c in data.columns if c not in EXPECTED_COLUMNS and c not in ['year', 'month', 'day']]
    data = data[front + extras + date_cols]
    
    applied_mappings = {k: v for k, v in rename_map.items() if k != v}
    if applied_mappings:
        logger.info(f"Applied column mappings: {applied_mappings}")
    
    return data


def _format_partial_date(df: pd.DataFrame) -> pd.Series:
    month_names = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    def format_row(row):
        year = row['year']
        month = row['month']
        day = row['day']
        
        has_year = pd.notna(year)
        has_month = pd.notna(month)
        has_day = pd.notna(day)
        
        if has_year and has_month and has_day:
            try:
                month_int = int(month)
                if 1 <= month_int <= 12:
                    return f"{month_names[month_int]} {int(day)}, {int(year)}"
            except (ValueError, TypeError):
                pass
        
        if has_year and has_month:
            try:
                month_int = int(month)
                if 1 <= month_int <= 12:
                    return f"{month_names[month_int]} {int(year)}"
            except (ValueError, TypeError):
                pass
        
        if has_year:
            try:
                return str(int(year))
            except (ValueError, TypeError):
                pass
        
        return "Date unknown"
    
    return df.apply(format_row, axis=1)