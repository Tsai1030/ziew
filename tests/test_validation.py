from kbparse.validation import validate_doc_output


def test_validation_fails_when_markdown_image_asset_missing(tmp_path):
    doc_dir = tmp_path / "doc1"
    doc_dir.mkdir()
    (doc_dir / "document.md").write_text("![圖片](assets/figures/missing.png)", encoding="utf-8")
    result = validate_doc_output(doc_dir)
    assert not result.ok
    assert any("missing.png" in issue.message for issue in result.issues)
