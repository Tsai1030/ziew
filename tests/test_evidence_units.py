from kbparse.chunking.builder import build_chunks
from tests.fixtures.sample_document_factory import make_sample_document


def test_evidence_unit_groups_figure_with_nearby_context():
    chunks = build_chunks(make_sample_document(), include_evidence_units=True)
    eu = next(c for c in chunks if c.chunk_type == "evidence_unit")
    assert "系統架構" in eu.text_for_embedding
    assert eu.related_assets == ["assets/figures/p0001_fig001.png"]
    assert "assets/" not in eu.text_for_embedding
