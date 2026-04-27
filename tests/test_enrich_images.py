from kbparse.enrichment.images import enrich_images
from kbparse.providers.mock_provider import MockVLMProvider
from tests.fixtures.sample_document_factory import make_sample_document


def test_enrich_images_updates_derived_fields_only():
    doc = make_sample_document()
    before = next(e for e in doc.elements if e.type == "figure")
    enriched = enrich_images(doc, MockVLMProvider())
    after = next(e for e in enriched.elements if e.type == "figure")

    assert after.description_status == "done"
    assert after.asset_path == before.asset_path
    assert after.bbox == before.bbox
    assert after.page == before.page
    assert after.enrichment["provider"] == "mock"


def test_enrich_images_failure_marks_failed():
    class BadProvider:
        name = "bad"
        model = "bad-model"
        def describe_image(self, image_path, prompt, context):
            raise RuntimeError("boom")

    enriched = enrich_images(make_sample_document(), BadProvider())
    fig = next(e for e in enriched.elements if e.type == "figure")
    assert fig.description_status == "failed"
    assert "boom" in fig.enrichment["error"]
