from typer.testing import CliRunner
from kbparse.cli import app


def test_e2e_fake_ingest_outputs_valid_assets_markdown_chunks(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "sample.pdf").write_bytes(b"%PDF-1.4 fake")
    out = tmp_path / "output"

    result = CliRunner().invoke(app, ["ingest", str(pdfs), str(out), "--parser", "fake", "--provider", "mock"])
    assert result.exit_code == 0, result.output

    doc_dir = out / "sample"
    assert (doc_dir / "document.json").exists()
    assert (doc_dir / "document.md").exists()
    assert (doc_dir / "chunks.jsonl").exists()
    assert (doc_dir / "assets" / "figures" / "p0001_fig001.png").exists()
    assert "Validation OK" in result.output
