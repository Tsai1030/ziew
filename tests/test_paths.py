from kbparse.paths import doc_output_paths
from kbparse.images.assets import make_asset_path


def test_doc_output_paths_are_relative_inside_doc_folder(tmp_path):
    paths = doc_output_paths(tmp_path, "doc1")
    assert paths.document_json.name == "document.json"
    assert paths.assets_dir.name == "assets"
    assert str(paths.doc_dir).endswith("doc1")


def test_make_figure_asset_path_uses_stable_naming():
    assert make_asset_path(page=3, kind="figure", index=2) == "assets/figures/p0003_fig002.png"
