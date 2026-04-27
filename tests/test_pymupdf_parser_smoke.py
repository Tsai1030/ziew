from __future__ import annotations

from pathlib import Path

import pymupdf
from PIL import Image

from kbparse.parsers.pymupdf_parser import PyMuPDFParser


def _make_pdf_with_text_and_image(path: Path, image_path: Path) -> None:
    image = Image.new("RGB", (80, 40), color=(200, 230, 255))
    image.save(image_path)

    doc = pymupdf.open()
    page = doc.new_page(width=300, height=220)
    page.insert_text((40, 50), "Hello KBParse PDF", fontsize=14)
    page.insert_text((40, 80), "Second paragraph", fontsize=12)
    page.insert_image(pymupdf.Rect(40, 100, 140, 150), filename=str(image_path))
    doc.save(path)
    doc.close()


def test_pymupdf_parser_extracts_text_and_renders_page_image(tmp_path):
    pdf = tmp_path / "real.pdf"
    embedded_image = tmp_path / "embedded.png"
    _make_pdf_with_text_and_image(pdf, embedded_image)

    out = tmp_path / "out" / "real"
    doc = PyMuPDFParser().parse(pdf, out)

    assert doc.doc_id == "real"
    assert doc.parser.name == "pymupdf"
    assert doc.pages[0].page_image_path == "parse_artifacts/pages/page_0001.png"
    assert (out / "parse_artifacts/pages/page_0001.png").exists()
    assert any(e.type == "paragraph" and "Hello KBParse PDF" in (e.text or "") for e in doc.elements)


def test_pymupdf_parser_extracts_embedded_images_as_assets(tmp_path):
    pdf = tmp_path / "with_image.pdf"
    embedded_image = tmp_path / "embedded.png"
    _make_pdf_with_text_and_image(pdf, embedded_image)

    out = tmp_path / "out" / "with_image"
    doc = PyMuPDFParser().parse(pdf, out)

    image_elements = [e for e in doc.elements if e.type == "image"]
    assert image_elements
    image = image_elements[0]
    assert image.asset_path == "assets/images/p0001_img001.png"
    assert image.description_status == "pending"
    assert (out / image.asset_path).exists()
    assert image.source and image.source["parser"] == "pymupdf"
