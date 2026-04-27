from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf
from PIL import Image

from kbparse.images.assets import make_asset_path, make_page_image_path
from kbparse.models import Document, Element, Page, ParserInfo, Source


class PyMuPDFParser:
    """Lightweight PDF parser for text-layer PDFs.

    This is intentionally a skeleton parser: it extracts text blocks, renders page
    images, and extracts embedded images as pending visual assets. Rich layout,
    OCR, and table structure are delegated to future Docling/Marker adapters.
    """

    name = "pymupdf"
    version = "0.1.0"

    def parse(self, pdf_path: str | Path, output_doc_dir: str | Path) -> Document:
        pdf_path = Path(pdf_path)
        output_doc_dir = Path(output_doc_dir)
        (output_doc_dir / "parse_artifacts" / "pages").mkdir(parents=True, exist_ok=True)
        (output_doc_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)

        sha = hashlib.sha256(pdf_path.read_bytes()).hexdigest() if pdf_path.exists() else None
        pages: list[Page] = []
        elements: list[Element] = []
        reading_order = 1

        with pymupdf.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                page_image_path = make_page_image_path(page_index)
                self._render_page(page, output_doc_dir / page_image_path)
                width = float(page.rect.width)
                height = float(page.rect.height)
                pages.append(Page(page_num=page_index, width=width, height=height, page_image_path=page_image_path))

                text_blocks = self._text_blocks(page)
                for text_idx, block in enumerate(text_blocks, start=1):
                    text = block[4].strip()
                    if not text:
                        continue
                    elements.append(
                        Element(
                            element_id=f"p{page_index:04d}_text{text_idx:03d}",
                            type="paragraph",
                            page=page_index,
                            bbox=self._normalize_bbox(block[:4], width, height),
                            reading_order=reading_order,
                            text=text,
                            section_path=[],
                            metadata={"parser_block_type": "text"},
                        )
                    )
                    reading_order += 1

                for image_idx, image_info in enumerate(self._image_infos(pdf, page), start=1):
                    asset_path = make_asset_path(page_index, "image", image_idx, ext="png")
                    self._save_image_png(image_info["image_bytes"], output_doc_dir / asset_path)
                    elements.append(
                        Element(
                            element_id=f"p{page_index:04d}_img{image_idx:03d}",
                            type="image",
                            page=page_index,
                            bbox=self._normalize_bbox(image_info["bbox"], width, height),
                            reading_order=reading_order,
                            section_path=[],
                            asset_path=asset_path,
                            markdown=f"![圖片：第 {page_index} 頁圖 {image_idx}，待描述]({asset_path})",
                            description_status="pending",
                            source={
                                "page_image": page_image_path,
                                "crop_method": "pymupdf_embedded_image",
                                "parser": self.name,
                                "xref": image_info["xref"],
                            },
                        )
                    )
                    reading_order += 1

        return Document(
            doc_id=pdf_path.stem,
            source=Source(path=str(pdf_path), sha256=sha),
            pages=pages,
            elements=elements,
            parser=ParserInfo(name=self.name, version=self.version),
        )

    def _render_page(self, page: pymupdf.Page, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        pix.save(output_path)

    def _text_blocks(self, page: pymupdf.Page) -> list[tuple]:
        blocks = page.get_text("blocks")
        # PyMuPDF block tuple: x0, y0, x1, y1, text, block_no, block_type
        text_blocks = [b for b in blocks if len(b) >= 7 and b[6] == 0]
        return sorted(text_blocks, key=lambda b: (b[1], b[0]))

    def _image_infos(self, pdf: pymupdf.Document, page: pymupdf.Page) -> list[dict]:
        infos: list[dict] = []
        seen: set[tuple[int, tuple[float, float, float, float]]] = set()
        for img in page.get_images(full=True):
            xref = int(img[0])
            extracted = pdf.extract_image(xref)
            image_bytes = extracted.get("image")
            if not image_bytes:
                continue
            rects = page.get_image_rects(xref) or [pymupdf.Rect(0, 0, 0, 0)]
            for rect in rects:
                bbox = (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))
                key = (xref, bbox)
                if key in seen:
                    continue
                seen.add(key)
                infos.append({"xref": xref, "bbox": bbox, "image_bytes": image_bytes})
        return sorted(infos, key=lambda info: (info["bbox"][1], info["bbox"][0]))

    def _save_image_png(self, image_bytes: bytes, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import io

            with Image.open(io.BytesIO(image_bytes)) as image:
                image.convert("RGB").save(output_path, format="PNG")
        except Exception:
            # If PIL cannot decode the embedded image, keep the raw bytes at the
            # requested path so validation still has a traceable asset.
            output_path.write_bytes(image_bytes)

    def _normalize_bbox(self, bbox: tuple | list, width: float, height: float) -> list[float]:
        x0, y0, x1, y1 = [float(v) for v in bbox]
        if width <= 0 or height <= 0:
            return [0.0, 0.0, 0.0, 0.0]
        return [
            round(max(0.0, min(1.0, x0 / width)), 6),
            round(max(0.0, min(1.0, y0 / height)), 6),
            round(max(0.0, min(1.0, x1 / width)), 6),
            round(max(0.0, min(1.0, y1 / height)), 6),
        ]
