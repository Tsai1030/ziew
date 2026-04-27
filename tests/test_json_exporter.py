from kbparse.exporters.json_exporter import save_document_json, load_document_json
from tests.fixtures.sample_document_factory import make_sample_document


def test_document_json_round_trip_preserves_asset_path(tmp_path):
    doc = make_sample_document()
    path = tmp_path / "document.json"
    save_document_json(doc, path)
    loaded = load_document_json(path)
    fig = next(e for e in loaded.elements if e.type == "figure")
    assert fig.asset_path == "assets/figures/p0001_fig001.png"
