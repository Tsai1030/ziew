from __future__ import annotations

import json
from pathlib import Path
from kbparse.models import Document


def save_document_json(doc: Document, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(doc.model_dump_json(indent=2), encoding="utf-8")


def load_document_json(path: str | Path) -> Document:
    return Document.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
