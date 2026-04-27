from kbparse.models import Element, Chunk


def test_figure_element_preserves_asset_metadata():
    el = Element(
        element_id="p0003_fig002",
        type="figure",
        page=3,
        bbox=[0.12, 0.28, 0.88, 0.61],
        reading_order=8,
        asset_path="assets/figures/p0003_fig002.png",
        description_status="pending",
    )
    assert el.asset_path == "assets/figures/p0003_fig002.png"
    assert el.description_status == "pending"


def test_visual_chunk_rejects_raw_path_in_embedding_text():
    chunk = Chunk(
        chunk_id="doc_p0003_fig002",
        doc_id="doc",
        chunk_type="visual",
        text="圖片：第 3 頁圖 2",
        text_for_embedding="圖片：系統架構圖。",
        markdown="![圖片](assets/figures/p0003_fig002.png)",
        asset_path="assets/figures/p0003_fig002.png",
        page=3,
        bbox=[0.12, 0.28, 0.88, 0.61],
        source_element_ids=["p0003_fig002"],
        do_not_split=True,
    )
    assert "assets/" not in chunk.text_for_embedding
