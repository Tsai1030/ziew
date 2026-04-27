from kbparse.enrichment.images import enrich_images
from tests.fixtures.sample_document_factory import make_sample_document


class RecordingProvider:
    name = "recording"
    model = "recording-model"

    def __init__(self):
        self.calls = []

    def describe_image(self, image_path, prompt, context):
        self.calls.append((image_path, context))
        return {
            "alt_text_short": "系統架構圖",
            "description_long": "此圖描述公司知識庫解析流程。",
            "confidence": 0.9,
            "needs_human_review": False,
        }


def test_enrich_images_resolves_relative_asset_path_from_doc_dir(tmp_path):
    doc_dir = tmp_path / "sample"
    asset = doc_dir / "assets" / "figures" / "p0001_fig001.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"fake-png")
    provider = RecordingProvider()

    enriched = enrich_images(make_sample_document(), provider, asset_root=doc_dir)

    assert provider.calls[0][0] == str(asset)
    fig = next(e for e in enriched.elements if e.type == "figure")
    assert fig.description_status == "done"
    assert fig.alt_text_short == "系統架構圖"
    assert fig.description_long == "此圖描述公司知識庫解析流程。"
