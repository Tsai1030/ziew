from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from kbparse.chunking.io import read_chunks_jsonl
from kbparse.exporters.json_exporter import load_document_json

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


@dataclass
class ValidationIssue:
    message: str
    severity: str = "error"


@dataclass
class ValidationResult:
    ok: bool
    issues: list[ValidationIssue] = field(default_factory=list)


def validate_doc_output(doc_dir: str | Path, require_chunks: bool = False) -> ValidationResult:
    doc_dir = Path(doc_dir)
    issues: list[ValidationIssue] = []
    document_json = doc_dir / "document.json"
    document_md = doc_dir / "document.md"
    chunks_path = doc_dir / "chunks.jsonl"

    if not document_json.exists():
        issues.append(ValidationIssue("document.json missing"))
    if not document_md.exists():
        issues.append(ValidationIssue("document.md missing"))
    if require_chunks and not chunks_path.exists():
        issues.append(ValidationIssue("chunks.jsonl missing"))

    if document_md.exists():
        md = document_md.read_text(encoding="utf-8")
        for link in IMG_RE.findall(md):
            if Path(link).is_absolute() or re.match(r"^[A-Za-z]:", link):
                issues.append(ValidationIssue(f"Markdown image link is absolute: {link}"))
            if not (doc_dir / link).exists():
                issues.append(ValidationIssue(f"Markdown image asset missing: {link}"))

    if document_json.exists():
        try:
            doc = load_document_json(document_json)
            for el in doc.elements:
                if el.type in {"figure", "image", "table_image"}:
                    if not el.asset_path:
                        issues.append(ValidationIssue(f"Visual element missing asset_path: {el.element_id}"))
                    elif not (doc_dir / el.asset_path).exists():
                        issues.append(ValidationIssue(f"Visual element asset missing: {el.asset_path}"))
                if el.type == "table" and el.asset_path and not (doc_dir / el.asset_path).exists():
                    issues.append(ValidationIssue(f"Table asset missing: {el.asset_path}"))
        except Exception as exc:
            issues.append(ValidationIssue(f"document.json invalid: {exc}"))

    if chunks_path.exists():
        try:
            for chunk in read_chunks_jsonl(chunks_path):
                if any(s in chunk.text_for_embedding.lower() for s in ["assets/", ".png", ".jpg", ".jpeg", ".webp"]):
                    issues.append(ValidationIssue(f"Embedding text contains image path: {chunk.chunk_id}"))
                if chunk.chunk_type == "visual" and (not chunk.asset_path or chunk.page is None or chunk.bbox is None or not chunk.do_not_split):
                    issues.append(ValidationIssue(f"Visual chunk missing required fields: {chunk.chunk_id}"))
                if not chunk.source_element_ids:
                    issues.append(ValidationIssue(f"Chunk missing source_element_ids: {chunk.chunk_id}"))
                if not chunk.doc_id or (chunk.page is None and chunk.page_range is None):
                    issues.append(ValidationIssue(f"Chunk missing traceability: {chunk.chunk_id}"))
        except Exception as exc:
            issues.append(ValidationIssue(f"chunks.jsonl invalid: {exc}"))

    return ValidationResult(ok=not issues, issues=issues)
