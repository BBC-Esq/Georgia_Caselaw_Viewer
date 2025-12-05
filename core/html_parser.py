from bs4 import BeautifulSoup
import logging
from utils.helpers import validate_and_resolve_path

logger = logging.getLogger(__name__)

def parse_html_content(file_path: str) -> str:
    try:
        path = validate_and_resolve_path(file_path, fallback_subdir="Caselaw")

        with open(path, "r", encoding="utf-8") as fh:
            soup = BeautifulSoup(fh, "html.parser")
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