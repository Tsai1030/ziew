from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from kbparse.chunking.builder import build_chunks
from kbparse.chunking.io import write_chunks_jsonl
from kbparse.enrichment.images import enrich_images
from kbparse.exporters.json_exporter import load_document_json, save_document_json
from kbparse.exporters.markdown import export_markdown
from kbparse.parsers.docling_parser import DoclingParser
from kbparse.parsers.fake_parser import FakeParser
from kbparse.parsers.pymupdf_parser import PyMuPDFParser
from kbparse.providers.mock_provider import MockVLMProvider
from kbparse.quality.report import build_quality_report
from kbparse.validation import validate_doc_output

app = typer.Typer(no_args_is_help=True)
console = Console()


def _parser(name: str):
    if name == "fake":
        return FakeParser()
    if name == "pymupdf":
        return PyMuPDFParser()
    if name == "docling":
        return DoclingParser()
    raise typer.BadParameter(f"Unsupported parser: {name}")


def _provider(name: str):
    if name == "mock":
        return MockVLMProvider()
    raise typer.BadParameter(f"Unsupported provider: {name}")


def _pdfs(pdf_input: Path) -> list[Path]:
    if pdf_input.is_file():
        return [pdf_input]
    return sorted(pdf_input.glob("*.pdf"))


def _write_report(doc, doc_dir: Path) -> None:
    result = validate_doc_output(doc_dir, require_chunks=(doc_dir / "chunks.jsonl").exists())
    report = build_quality_report(doc, doc_dir, validation_ok=result.ok, issues=[i.message for i in result.issues])
    (doc_dir / "quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_one(pdf: Path, output_root: Path, parser_name: str):
    doc_dir = output_root / pdf.stem
    parser = _parser(parser_name)
    try:
        doc = parser.parse(pdf, doc_dir)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    save_document_json(doc, doc_dir / "document.json")
    (doc_dir / "document.md").write_text(export_markdown(doc), encoding="utf-8")
    _write_report(doc, doc_dir)
    return doc_dir


@app.command("parse")
def parse_command(pdf_input: Path, output_root: Path, parser: str = typer.Option("fake", "--parser")):
    """Parse PDFs into document.json/document.md plus assets."""
    if not pdf_input.exists():
        raise typer.BadParameter(f"Input does not exist: {pdf_input}")
    output_root.mkdir(parents=True, exist_ok=True)
    docs = [_parse_one(pdf, output_root, parser) for pdf in _pdfs(pdf_input)]
    console.print(f"Parsed {len(docs)} document(s)")


@app.command("build-chunks")
def build_chunks_command(doc_dir: Path):
    doc = load_document_json(doc_dir / "document.json")
    chunks = build_chunks(doc, include_evidence_units=True)
    write_chunks_jsonl(chunks, doc_dir / "chunks.jsonl")
    _write_report(doc, doc_dir)
    console.print(f"Wrote {len(chunks)} chunks")


@app.command("enrich-images")
def enrich_images_command(doc_dir: Path, provider: str = typer.Option("mock", "--provider")):
    doc = load_document_json(doc_dir / "document.json")
    enriched = enrich_images(doc, _provider(provider))
    save_document_json(enriched, doc_dir / "document.json")
    (doc_dir / "document.md").write_text(export_markdown(enriched), encoding="utf-8")
    if (doc_dir / "chunks.jsonl").exists():
        write_chunks_jsonl(build_chunks(enriched, include_evidence_units=True), doc_dir / "chunks.jsonl")
    _write_report(enriched, doc_dir)
    console.print("Enriched images")


@app.command("validate")
def validate_command(doc_dir: Path):
    result = validate_doc_output(doc_dir, require_chunks=(doc_dir / "chunks.jsonl").exists())
    if result.ok:
        console.print("Validation OK")
        raise typer.Exit(0)
    for issue in result.issues:
        console.print(f"Validation issue: {issue.message}")
    raise typer.Exit(1)


@app.command("ingest")
def ingest_command(pdf_input: Path, output_root: Path, parser: str = typer.Option("fake", "--parser"), provider: str = typer.Option("mock", "--provider")):
    if not pdf_input.exists():
        raise typer.BadParameter(f"Input does not exist: {pdf_input}")
    output_root.mkdir(parents=True, exist_ok=True)
    doc_dirs = [_parse_one(pdf, output_root, parser) for pdf in _pdfs(pdf_input)]
    for doc_dir in doc_dirs:
        doc = load_document_json(doc_dir / "document.json")
        enriched = enrich_images(doc, _provider(provider))
        save_document_json(enriched, doc_dir / "document.json")
        (doc_dir / "document.md").write_text(export_markdown(enriched), encoding="utf-8")
        write_chunks_jsonl(build_chunks(enriched, include_evidence_units=True), doc_dir / "chunks.jsonl")
        _write_report(enriched, doc_dir)
        result = validate_doc_output(doc_dir, require_chunks=True)
        if not result.ok:
            for issue in result.issues:
                console.print(f"Validation issue: {issue.message}")
            raise typer.Exit(1)
    console.print("Validation OK")
