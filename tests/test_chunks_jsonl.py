import json
from kbparse.chunking.builder import build_chunks
from kbparse.chunking.io import write_chunks_jsonl, read_chunks_jsonl
from tests.fixtures.sample_document_factory import make_sample_document


def test_chunks_jsonl_each_line_is_valid_json(tmp_path):
    chunks = build_chunks(make_sample_document())
    path = tmp_path / "chunks.jsonl"
    write_chunks_jsonl(chunks, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        json.loads(line)


def test_chunks_jsonl_round_trip_preserves_visual_asset_path(tmp_path):
    chunks = build_chunks(make_sample_document())
    path = tmp_path / "chunks.jsonl"
    write_chunks_jsonl(chunks, path)
    loaded = read_chunks_jsonl(path)
    visual = next(c for c in loaded if c.chunk_type == "visual")
    assert visual.asset_path == "assets/figures/p0001_fig001.png"
