from __future__ import annotations

from pathlib import Path
from typing import Protocol

from kbparse.models import Document


class Parser(Protocol):
    name: str
    version: str
    def parse(self, pdf_path: str | Path, output_doc_dir: str | Path) -> Document: ...
