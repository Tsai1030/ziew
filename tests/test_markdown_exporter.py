from kbparse.exporters.markdown import export_markdown
from tests.fixtures.sample_document_factory import make_sample_document


def test_exports_standard_markdown_image_syntax():
    md = export_markdown(make_sample_document())
    assert "![圖片：第 1 頁圖 1，待描述](assets/figures/p0001_fig001.png)" in md


def test_pending_image_includes_description_placeholder():
    md = export_markdown(make_sample_document())
    assert "> 圖片描述：尚未產生，等待 VLM enrichment。" in md


def test_markdown_does_not_use_absolute_asset_paths():
    md = export_markdown(make_sample_document())
    assert "/mnt/" not in md
    assert "C:\\" not in md
