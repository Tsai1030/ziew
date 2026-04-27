from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocOutputPaths:
    doc_dir: Path
    document_json: Path
    document_md: Path
    chunks_jsonl: Path
    quality_report: Path
    parse_artifacts_dir: Path
    pages_dir: Path
    assets_dir: Path
    figures_dir: Path
    images_dir: Path
    tables_dir: Path


def doc_output_paths(output_root: str | Path, doc_id: str) -> DocOutputPaths:
    doc_dir = Path(output_root) / doc_id
    return DocOutputPaths(
        doc_dir=doc_dir,
        document_json=doc_dir / "document.json",
        document_md=doc_dir / "document.md",
        chunks_jsonl=doc_dir / "chunks.jsonl",
        quality_report=doc_dir / "quality_report.json",
        parse_artifacts_dir=doc_dir / "parse_artifacts",
        pages_dir=doc_dir / "parse_artifacts" / "pages",
        assets_dir=doc_dir / "assets",
        figures_dir=doc_dir / "assets" / "figures",
        images_dir=doc_dir / "assets" / "images",
        tables_dir=doc_dir / "assets" / "tables",
    )


def ensure_doc_dirs(paths: DocOutputPaths) -> None:
    for p in [paths.doc_dir, paths.pages_dir, paths.figures_dir, paths.images_dir, paths.tables_dir]:
        p.mkdir(parents=True, exist_ok=True)
