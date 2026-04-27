from kbparse.chunking.builder import build_chunks
from tests.fixtures.sample_document_factory import make_sample_document


def test_table_chunk_is_atomic():
    chunks = build_chunks(make_sample_document())
    table = next(c for c in chunks if c.chunk_type == "table")
    assert table.do_not_split is True
    assert table.source_element_ids


def test_code_chunk_is_atomic():
    chunks = build_chunks(make_sample_document())
    code = next(c for c in chunks if c.chunk_type == "code")
    assert code.do_not_split is True
    assert "```" in code.markdown
