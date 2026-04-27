from __future__ import annotations

import json

import pymupdf
import pytest
from kbparse.chunking.builder import build_chunks
from kbparse.exporters.markdown import export_markdown

from kbparse.parsers.docling_parser import DoclingParser


class _FakeDoclingDocument:
    def export_to_markdown(self):
        return "# Markdown Fallback Title\n\nMarkdown fallback paragraph."

    def export_to_dict(self):
        return {
            "pages": {"1": {"size": {"width": 300, "height": 200}}},
            "origin": "fake-docling",
            "body": {
                "children": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                    {"$ref": "#/tables/0"},
                ]
            },
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "section_header",
                    "text": "Docling Direct Title",
                    "prov": [{"page_no": 1, "bbox": {"l": 30, "t": 180, "r": 270, "b": 160, "coord_origin": "BOTTOMLEFT"}}],
                },
                {
                    "self_ref": "#/texts/1",
                    "label": "text",
                    "text": "Docling direct paragraph.",
                    "prov": [{"page_no": 1, "bbox": {"l": 30, "t": 150, "r": 250, "b": 130, "coord_origin": "BOTTOMLEFT"}}],
                },
                {
                    "self_ref": "#/texts/2",
                    "label": "caption",
                    "text": "表 1：測試表格",
                    "prov": [{"page_no": 1, "bbox": {"l": 30, "t": 120, "r": 180, "b": 108, "coord_origin": "BOTTOMLEFT"}}],
                },
            ],
            "tables": [
                {
                    "self_ref": "#/tables/0",
                    "label": "table",
                    "prov": [{"page_no": 1, "bbox": {"l": 30, "t": 100, "r": 200, "b": 60, "coord_origin": "BOTTOMLEFT"}}],
                    "data": {"table_cells": [
                        {"row_header": False, "column_header": True, "start_row_offset_idx": 0, "end_row_offset_idx": 1, "start_col_offset_idx": 0, "end_col_offset_idx": 1, "text": "A"},
                        {"row_header": False, "column_header": True, "start_row_offset_idx": 0, "end_row_offset_idx": 1, "start_col_offset_idx": 1, "end_col_offset_idx": 2, "text": "B"},
                        {"row_header": False, "column_header": False, "start_row_offset_idx": 1, "end_row_offset_idx": 2, "start_col_offset_idx": 0, "end_col_offset_idx": 1, "text": "1"},
                        {"row_header": False, "column_header": False, "start_row_offset_idx": 1, "end_row_offset_idx": 2, "start_col_offset_idx": 1, "end_col_offset_idx": 2, "text": "2"},
                    ]},
                }
            ],
        }


class _FakeConversionResult:
    document = _FakeDoclingDocument()


class _FakeConverter:
    def convert(self, source):
        self.source = source
        return _FakeConversionResult()


def test_docling_parser_maps_layout_tree_to_canonical_elements_and_raw_artifact(tmp_path):
    pdf = tmp_path / "docling.pdf"
    pdf.write_bytes(b"%PDF-1.4 docling fake")
    out = tmp_path / "out"

    doc = DoclingParser(converter_factory=_FakeConverter).parse(pdf, out)

    assert doc.doc_id == "docling"
    assert doc.parser.name == "docling"
    assert doc.pages[0].page_num == 1
    assert doc.pages[0].width == 300
    assert doc.pages[0].height == 200
    assert [el.type for el in doc.elements] == ["heading", "paragraph", "caption", "table"]
    assert [el.text for el in doc.elements[:3]] == ["Docling Direct Title", "Docling direct paragraph.", "表 1：測試表格"]
    assert doc.elements[0].metadata["level"] == 1
    assert doc.elements[0].metadata["docling_ref"] == "#/texts/0"
    assert doc.elements[0].bbox == [0.1, 0.1, 0.9, 0.2]
    assert doc.elements[2].metadata["parser_block_type"] == "docling_caption"
    assert doc.elements[3].metadata["parser_block_type"] == "docling_table"
    assert doc.elements[3].text == "| A | B |\n| --- | --- |\n| 1 | 2 |"
    assert doc.elements[3].page == 1
    assert doc.elements[3].bbox == [0.1, 0.5, 0.666667, 0.7]
    raw = json.loads((out / "parse_artifacts" / "docling_document.json").read_text(encoding="utf-8"))
    assert raw["origin"] == "fake-docling"


def test_docling_parser_missing_dependency_has_helpful_message(tmp_path):
    def missing_converter():
        raise ImportError("No module named 'docling'")

    with pytest.raises(RuntimeError, match="Install Docling"):
        DoclingParser(converter_factory=missing_converter).parse(tmp_path / "x.pdf", tmp_path / "out")


class _FakePictureDoclingDocument:
    def export_to_markdown(self):
        return ""

    def export_to_dict(self):
        return {
            "pages": {"1": {"size": {"width": 300, "height": 200}}},
            "body": {
                "children": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/pictures/0"},
                    {"$ref": "#/texts/1"},
                ]
            },
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "text",
                    "text": "上方段落說明系統架構。",
                    "prov": [{"page_no": 1, "bbox": {"l": 30, "t": 180, "r": 260, "b": 160, "coord_origin": "BOTTOMLEFT"}}],
                },
                {
                    "self_ref": "#/texts/1",
                    "label": "caption",
                    "text": "圖 1：系統架構圖",
                    "prov": [{"page_no": 1, "bbox": {"l": 40, "t": 52, "r": 180, "b": 40, "coord_origin": "BOTTOMLEFT"}}],
                },
            ],
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "label": "picture",
                    "prov": [{"page_no": 1, "bbox": {"l": 40, "t": 150, "r": 180, "b": 70, "coord_origin": "BOTTOMLEFT"}}],
                }
            ],
            "tables": [],
        }


class _FakePictureConversionResult:
    document = _FakePictureDoclingDocument()


class _FakePictureConverter:
    def convert(self, source):
        return _FakePictureConversionResult()


def _make_picture_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((30, 30), "Architecture diagram", fontsize=12)
    page.draw_rect(pymupdf.Rect(40, 50, 180, 130), color=(1, 0, 0), fill=(1, 0.85, 0.85))
    page.insert_text((48, 92), "API -> DB", fontsize=14)
    page.insert_text((40, 160), "Figure 1 architecture", fontsize=10)
    doc.save(path)
    doc.close()


def test_docling_parser_crops_picture_assets_and_associates_caption(tmp_path):
    pdf = tmp_path / "picture.pdf"
    _make_picture_pdf(pdf)
    out = tmp_path / "out"

    doc = DoclingParser(converter_factory=_FakePictureConverter).parse(pdf, out)

    figure = next(el for el in doc.elements if el.type == "figure")
    assert figure.asset_path == "assets/figures/p0001_fig001.png"
    assert (out / figure.asset_path).exists()
    assert figure.caption_nearby == "圖 1：系統架構圖"
    assert figure.description_status == "pending"
    assert figure.markdown == "![圖片：第 1 頁圖 1，待描述](assets/figures/p0001_fig001.png)"
    assert figure.bbox == [0.133333, 0.25, 0.6, 0.65]
    assert figure.metadata["parser_block_type"] == "docling_picture"
    md = export_markdown(doc)
    assert "![圖片：第 1 頁圖 1，待描述](assets/figures/p0001_fig001.png)" in md
    chunks = build_chunks(doc, include_evidence_units=True)
    visual = next(chunk for chunk in chunks if chunk.chunk_type == "visual")
    assert visual.asset_path == figure.asset_path
    assert visual.do_not_split is True
    assert "assets/" not in visual.text_for_embedding


class _FakeTableDoclingDocument:
    def export_to_markdown(self):
        return ""

    def export_to_dict(self):
        return {
            "pages": {"1": {"size": {"width": 320, "height": 240}}},
            "body": {"children": [{"$ref": "#/texts/0"}, {"$ref": "#/tables/0"}]},
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "caption",
                    "text": "表 1：季度營收",
                    "prov": [{"page_no": 1, "bbox": {"l": 40, "t": 205, "r": 180, "b": 190, "coord_origin": "BOTTOMLEFT"}}],
                }
            ],
            "tables": [
                {
                    "self_ref": "#/tables/0",
                    "label": "table",
                    "prov": [{"page_no": 1, "bbox": {"l": 40, "t": 180, "r": 260, "b": 90, "coord_origin": "BOTTOMLEFT"}}],
                    "data": {
                        "table_cells": [
                            {"column_header": True, "start_row_offset_idx": 0, "end_row_offset_idx": 1, "start_col_offset_idx": 0, "end_col_offset_idx": 1, "text": "Quarter"},
                            {"column_header": True, "start_row_offset_idx": 0, "end_row_offset_idx": 1, "start_col_offset_idx": 1, "end_col_offset_idx": 2, "text": "Revenue"},
                            {"column_header": False, "start_row_offset_idx": 1, "end_row_offset_idx": 2, "start_col_offset_idx": 0, "end_col_offset_idx": 1, "text": "Q1"},
                            {"column_header": False, "start_row_offset_idx": 1, "end_row_offset_idx": 2, "start_col_offset_idx": 1, "end_col_offset_idx": 2, "text": "100"},
                        ],
                        "html": "<table><tr><th>Quarter</th><th>Revenue</th></tr><tr><td>Q1</td><td>100</td></tr></table>",
                    },
                }
            ],
            "pictures": [],
        }


class _FakeTableConversionResult:
    document = _FakeTableDoclingDocument()


class _FakeTableConverter:
    def convert(self, source):
        return _FakeTableConversionResult()


def _make_table_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=320, height=240)
    page.insert_text((40, 35), "Table 1 quarterly revenue", fontsize=10)
    table_rect = pymupdf.Rect(40, 60, 260, 150)
    page.draw_rect(table_rect, color=(0, 0, 1), fill=(0.9, 0.95, 1))
    page.draw_line((40, 90), (260, 90), color=(0, 0, 1))
    page.draw_line((150, 60), (150, 150), color=(0, 0, 1))
    page.insert_text((55, 80), "Quarter", fontsize=10)
    page.insert_text((165, 80), "Revenue", fontsize=10)
    page.insert_text((55, 120), "Q1", fontsize=10)
    page.insert_text((165, 120), "100", fontsize=10)
    doc.save(path)
    doc.close()


def test_docling_parser_crops_table_asset_and_preserves_structure(tmp_path):
    pdf = tmp_path / "table.pdf"
    _make_table_pdf(pdf)
    out = tmp_path / "out"

    doc = DoclingParser(converter_factory=_FakeTableConverter).parse(pdf, out)

    table = next(el for el in doc.elements if el.type == "table")
    assert table.asset_path == "assets/tables/p0001_table001.png"
    assert (out / table.asset_path).exists()
    assert (out / table.asset_path).read_bytes().startswith(b"\x89PNG")
    assert table.caption_nearby == "表 1：季度營收"
    assert table.metadata["parser_block_type"] == "docling_table"
    assert table.metadata["table_html"].startswith("<table>")
    assert table.metadata["table_cells"][0]["text"] == "Quarter"
    assert table.source["crop_method"] == "docling_bbox_page_render"

    chunks = build_chunks(doc, include_evidence_units=True)
    table_chunk = next(chunk for chunk in chunks if chunk.chunk_type == "table")
    assert table_chunk.asset_path == table.asset_path
    assert table_chunk.do_not_split is True
    assert "assets/" not in table_chunk.text_for_embedding
    evidence = next(chunk for chunk in chunks if chunk.chunk_type == "evidence_unit" and table.element_id in chunk.source_element_ids)
    assert table.asset_path in evidence.related_assets
    assert "assets/" not in evidence.text_for_embedding
