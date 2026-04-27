from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw

from kbparse.images.assets import make_asset_path, make_page_image_path
from kbparse.models import Document, Element, Page, ParserInfo, Source


class FakeParser:
    name = "fake_parser"
    version = "0.1.0"

    def parse(self, pdf_path: str | Path, output_doc_dir: str | Path) -> Document:
        pdf_path = Path(pdf_path)
        output_doc_dir = Path(output_doc_dir)
        (output_doc_dir / "assets" / "figures").mkdir(parents=True, exist_ok=True)
        (output_doc_dir / "parse_artifacts" / "pages").mkdir(parents=True, exist_ok=True)

        asset_path = make_asset_path(1, "figure", 1)
        page_image_path = make_page_image_path(1)
        self._placeholder(output_doc_dir / asset_path, "FIGURE")
        self._placeholder(output_doc_dir / page_image_path, "PAGE 1", size=(612, 792))

        sha = hashlib.sha256(pdf_path.read_bytes()).hexdigest() if pdf_path.exists() else None
        doc_id = pdf_path.stem
        return Document(
            doc_id=doc_id,
            source=Source(path=str(pdf_path), sha256=sha),
            pages=[Page(page_num=1, width=612, height=792, page_image_path=page_image_path)],
            parser=ParserInfo(name=self.name, version=self.version),
            elements=[
                Element(element_id="p0001_h001", type="heading", page=1, bbox=[0.1, 0.05, 0.9, 0.1], reading_order=1, text="系統架構", section_path=["系統架構"]),
                Element(element_id="p0001_text001", type="paragraph", page=1, bbox=[0.1, 0.12, 0.9, 0.18], reading_order=2, text="本文件由 fake parser 產生，用於驗證端到端流程。", section_path=["系統架構"]),
                Element(element_id="p0001_fig001", type="figure", page=1, bbox=[0.1, 0.2, 0.9, 0.5], reading_order=3, section_path=["系統架構"], asset_path=asset_path, markdown=f"![圖片：第 1 頁圖 1，待描述]({asset_path})", caption_nearby="系統架構圖", description_status="pending", source={"page_image": page_image_path, "crop_method": "fake_placeholder", "parser": self.name}),
                Element(element_id="p0001_cap001", type="caption", page=1, bbox=[0.1, 0.51, 0.9, 0.55], reading_order=4, text="圖 1：系統架構圖", section_path=["系統架構"]),
                Element(element_id="p0001_text002", type="paragraph", page=1, bbox=[0.1, 0.56, 0.9, 0.62], reading_order=5, text="此圖展示資料流與服務邊界。", section_path=["系統架構"]),
                Element(element_id="p0001_table001", type="table", page=1, bbox=[0.1, 0.63, 0.9, 0.75], reading_order=6, text="| 元件 | 功能 |\n| --- | --- |\n| API | 接收請求 |", section_path=["系統架構"]),
                Element(element_id="p0001_code001", type="code", page=1, bbox=[0.1, 0.76, 0.9, 0.86], reading_order=7, text="print('kbparse')", section_path=["系統架構"], metadata={"language": "python"}),
            ],
        )

    def _placeholder(self, path: Path, label: str, size=(320, 180)) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", size, color=(245, 245, 245))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(80, 80, 80), width=3)
        draw.text((20, 20), label, fill=(0, 0, 0))
        img.save(path)
