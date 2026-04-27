from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from kbparse.models import Document
from kbparse.validation import validate_doc_output


def build_quality_report(doc: Document, doc_dir: str | Path | None = None, validation_ok: bool | None = None, issues: list[str] | None = None) -> dict[str, Any]:
    counts = Counter(e.type for e in doc.elements)
    asset_count = sum(1 for e in doc.elements if e.asset_path)
    missing_asset_count = 0
    if doc_dir is not None:
        root = Path(doc_dir)
        missing_asset_count = sum(1 for e in doc.elements if e.asset_path and not (root / e.asset_path).exists())
    if validation_ok is None:
        validation_ok = True
        if doc_dir is not None:
            result = validate_doc_output(doc_dir)
            validation_ok = result.ok
            issues = [i.message for i in result.issues]
    return {
        "doc_id": doc.doc_id,
        "parser": doc.parser.name,
        "page_count": len(doc.pages),
        "element_counts": dict(counts),
        "asset_count": asset_count,
        "missing_asset_count": missing_asset_count,
        "pending_description_count": sum(1 for e in doc.elements if e.description_status == "pending"),
        "validation_ok": bool(validation_ok),
        "issues": issues or [],
    }
