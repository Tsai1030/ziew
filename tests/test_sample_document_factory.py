from tests.fixtures.sample_document_factory import make_sample_document


def test_sample_document_has_visual_and_atomic_elements():
    doc = make_sample_document()
    types = [e.type for e in doc.elements]
    assert "figure" in types
    assert "table" in types
    assert "code" in types
