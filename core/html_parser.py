from pathlib import Path
from bs4 import BeautifulSoup
import logging
from utils.helpers import validate_and_resolve_path

logger = logging.getLogger(__name__)

def _read_with_fallback_encoding(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, ValueError):
            continue
    return path.read_bytes().decode("utf-8", errors="replace")

def parse_html_content(file_path: str) -> str:
    try:
        path = validate_and_resolve_path(file_path, fallback_subdir="Caselaw")
        raw = _read_with_fallback_encoding(path)
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        lines  = (ln.strip()   for ln in text.splitlines())
        chunks = (ph.strip()   for ln in lines for ph in ln.split("  "))
        return " ".join(ch for ch in chunks if ch)
    except FileNotFoundError:
        logger.error(f"HTML file not found: {file_path}", exc_info=True)
        raise
    except (IOError, OSError) as e:
        logger.error(f"Error reading HTML file {file_path}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error parsing HTML file {file_path}: {e}", exc_info=True)
        raise