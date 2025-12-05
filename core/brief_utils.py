from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from config.settings import settings

DEFAULT_TEMPERATURE = 0.3

@dataclass
class BriefRequest:
    file_path: str
    citation: str
    template: str
    model: str
    verbosity: str = "medium"
    temperature: float = DEFAULT_TEMPERATURE
    max_output_tokens: Optional[int] = None

def build_prompt(request: BriefRequest, case_text: str) -> str:
    return f"{request.template}\n\n{request.citation}\n\n{case_text}"

def build_brief_filename(html_path: str, ext: str) -> str:
    return f"{Path(html_path).stem}_brief.{ext}"

def ensure_unique_path(dir_path: Path, filename: str) -> Path:
    candidate = Path(dir_path) / filename
    if not candidate.exists():
        return candidate
    base, suffix = candidate.stem, candidate.suffix
    i = 1
    while (new := dir_path / f"{base}_{i}{suffix}").exists():
        i += 1
    return new

def build_brief_path(html_file: str, ext: str) -> Path:
    dir_path = Path(settings.briefs_save_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    filename = build_brief_filename(html_file, ext)
    return ensure_unique_path(dir_path, filename)