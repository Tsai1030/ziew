from kbparse.models import Document, Element, Page, ParserInfo, Source


def make_sample_document() -> Document:
    return Document(
        doc_id="sample",
        source=Source(path="sample.pdf", sha256="fake", mime_type="application/pdf"),
        pages=[Page(page_num=1, width=612, height=792, page_image_path="parse_artifacts/pages/page_0001.png")],
        parser=ParserInfo(name="fake_parser", version="0.1.0"),
        elements=[
            Element(element_id="p0001_h001", type="heading", page=1, bbox=[0.1, 0.05, 0.9, 0.1], reading_order=1, text="系統架構", section_path=["系統架構"]),
            Element(element_id="p0001_text001", type="paragraph", page=1, bbox=[0.1, 0.12, 0.9, 0.18], reading_order=2, text="本章說明系統架構與主要元件。", section_path=["系統架構"]),
            Element(
                element_id="p0001_fig001",
                type="figure",
                page=1,
                bbox=[0.1, 0.2, 0.9, 0.5],
                reading_order=3,
                section_path=["系統架構"],
                asset_path="assets/figures/p0001_fig001.png",
                markdown="![圖片：第 1 頁圖 1，待描述](assets/figures/p0001_fig001.png)",
                caption_nearby="系統架構圖",
                description_status="pending",
                source={"page_image": "parse_artifacts/pages/page_0001.png", "crop_method": "fake", "parser": "fake_parser"},
            ),
            Element(element_id="p0001_cap001", type="caption", page=1, bbox=[0.1, 0.51, 0.9, 0.55], reading_order=4, text="圖 1：系統架構圖", section_path=["系統架構"]),
            Element(element_id="p0001_text002", type="paragraph", page=1, bbox=[0.1, 0.56, 0.9, 0.62], reading_order=5, text="資料會由入口服務流向處理佇列，再進入索引服務。", section_path=["系統架構"]),
            Element(element_id="p0001_table001", type="table", page=1, bbox=[0.1, 0.63, 0.9, 0.75], reading_order=6, text="| 元件 | 功能 |\n| --- | --- |\n| API | 接收請求 |\n| Worker | 處理任務 |", section_path=["系統架構"]),
            Element(element_id="p0001_code001", type="code", page=1, bbox=[0.1, 0.76, 0.9, 0.86], reading_order=7, text="def hello():\n    return 'kbparse'", section_path=["系統架構"], metadata={"language": "python"}),
        ],
    )
