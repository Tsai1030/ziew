from kbparse.chunking.builder import build_chunks
from tests.fixtures.sample_document_factory import make_sample_document


def test_builds_visual_chunk_for_figure():
    chunks = build_chunks(make_sample_document())
    visual = next(c for c in chunks if c.chunk_type == "visual")
    assert visual.asset_path == "assets/figures/p0001_fig001.png"
    assert visual.do_not_split is True
    assert visual.page == 1
    assert visual.bbox == [0.1, 0.2, 0.9, 0.5]


def test_visual_chunk_embedding_text_excludes_raw_path():
    chunks = build_chunks(make_sample_document())
    visual = next(c for c in chunks if c.chunk_type == "visual")
    assert "assets/" not in visual.text_for_embedding
    assert ".png" not in visual.text_for_embedding


def test_chunks_have_source_and_doc_traceability():
    chunks = build_chunks(make_sample_document())
    assert all(c.source_element_ids for c in chunks)
    assert all(c.doc_id == "sample" for c in chunks)
    assert all(c.page is not None or c.page_range is not None for c in chunks)
