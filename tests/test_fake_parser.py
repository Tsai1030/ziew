from kbparse.parsers.fake_parser import FakeParser


def test_fake_parser_creates_document_with_existing_asset(tmp_path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    out = tmp_path / "out" / "doc1"
    doc = FakeParser().parse(pdf, out)
    fig = next(e for e in doc.elements if e.type == "figure")
    assert (out / fig.asset_path).exists()
    assert (out / "parse_artifacts" / "pages" / "page_0001.png").exists()
