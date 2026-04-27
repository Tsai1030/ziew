import pymupdf
from typer.testing import CliRunner
from kbparse.cli import app
from kbparse.parsers import docling_parser

runner = CliRunner()


def _make_text_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=160)
    page.insert_text((40, 50), "CLI PyMuPDF text", fontsize=14)
    doc.save(path)
    doc.close()


def test_cli_parse_fake_creates_outputs(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "sample.pdf").write_bytes(b"%PDF-1.4 fake")
    out = tmp_path / "output"
    result = runner.invoke(app, ["parse", str(pdfs), str(out), "--parser", "fake"])
    assert result.exit_code == 0, result.output
    doc_dir = out / "sample"
    assert (doc_dir / "document.json").exists()
    assert (doc_dir / "document.md").exists()
    assert (doc_dir / "quality_report.json").exists()


def test_cli_build_enrich_validate_contract(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "sample.pdf").write_bytes(b"%PDF-1.4 fake")
    out = tmp_path / "output"
    assert runner.invoke(app, ["parse", str(pdfs), str(out), "--parser", "fake"]).exit_code == 0
    doc_dir = out / "sample"
    assert runner.invoke(app, ["build-chunks", str(doc_dir)]).exit_code == 0
    assert runner.invoke(app, ["enrich-images", str(doc_dir), "--provider", "mock"]).exit_code == 0
    result = runner.invoke(app, ["validate", str(doc_dir)])
    assert result.exit_code == 0, result.output
    assert "Validation OK" in result.output


def test_cli_parse_pymupdf_creates_text_pdf_outputs(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    _make_text_pdf(pdfs / "real.pdf")
    out = tmp_path / "output"

    result = runner.invoke(app, ["parse", str(pdfs), str(out), "--parser", "pymupdf"])

    assert result.exit_code == 0, result.output
    doc_dir = out / "real"
    assert (doc_dir / "document.json").exists()
    assert (doc_dir / "document.md").exists()
    assert (doc_dir / "parse_artifacts/pages/page_0001.png").exists()
    assert "CLI PyMuPDF text" in (doc_dir / "document.md").read_text(encoding="utf-8")


class _CliFakeDoclingDocument:
    def export_to_markdown(self):
        return "# CLI Docling text\n\nParsed through Docling adapter."

    def export_to_dict(self):
        return {"pages": [{"size": {"width": 300, "height": 160}}]}


class _CliFakeResult:
    document = _CliFakeDoclingDocument()


def test_cli_parse_docling_creates_outputs(monkeypatch, tmp_path):
    class FakeDoclingParser(docling_parser.DoclingParser):
        def __init__(self):
            super().__init__(converter_factory=lambda: type("Converter", (), {"convert": lambda self, source: _CliFakeResult()})())

    monkeypatch.setattr("kbparse.cli.DoclingParser", FakeDoclingParser)
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "docling.pdf").write_bytes(b"%PDF-1.4 fake docling")
    out = tmp_path / "output"

    result = runner.invoke(app, ["parse", str(pdfs), str(out), "--parser", "docling"])

    assert result.exit_code == 0, result.output
    doc_dir = out / "docling"
    assert (doc_dir / "document.json").exists()
    assert (doc_dir / "document.md").exists()
    assert (doc_dir / "parse_artifacts/docling_document.json").exists()
    assert "CLI Docling text" in (doc_dir / "document.md").read_text(encoding="utf-8")


def test_cli_parse_docling_missing_dependency_shows_helpful_error(monkeypatch, tmp_path):
    class MissingDoclingParser:
        name = "docling"
        version = "0.1.0"

        def parse(self, pdf_path, output_doc_dir):
            raise RuntimeError("Install Docling to use --parser docling")

    monkeypatch.setattr("kbparse.cli.DoclingParser", MissingDoclingParser)
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "docling.pdf").write_bytes(b"%PDF-1.4 fake docling")

    result = runner.invoke(app, ["parse", str(pdfs), str(tmp_path / "out"), "--parser", "docling"])

    assert result.exit_code != 0
    assert "Install Docling" in result.output
    assert "Traceback" not in result.output
