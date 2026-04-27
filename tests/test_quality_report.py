from kbparse.quality.report import build_quality_report
from tests.fixtures.sample_document_factory import make_sample_document


def test_quality_report_counts_elements_and_pending_assets(tmp_path):
    doc = make_sample_document()
    report = build_quality_report(doc, tmp_path)
    assert report["doc_id"] == "sample"
    assert report["page_count"] == 1
    assert report["element_counts"]["figure"] == 1
    assert report["pending_description_count"] == 1
