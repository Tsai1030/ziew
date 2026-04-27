import pytest
from tests.fixtures.sample_document_factory import make_sample_document


@pytest.fixture
def sample_document():
    return make_sample_document()
