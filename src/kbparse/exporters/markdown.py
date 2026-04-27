from __future__ import annotations

from kbparse.models import Document, Element


def _alt(el: Element) -> str:
    if el.alt_text_short:
        return el.alt_text_short
    if el.caption_nearby and el.description_status == "done":
        return el.caption_nearby
    if el.page:
        # p0001_fig001 -> 1
        idx = el.element_id.split("fig")[-1].lstrip("0") or "1"
        return f"圖片：第 {el.page} 頁圖 {idx}，待描述"
    return "圖片，待描述"


def _element_markdown(el: Element) -> str:
    text = el.text or ""
    if el.type == "heading":
        level = int(el.metadata.get("level", 1)) if el.metadata else 1
        return f"{'#' * max(1, min(level, 6))} {text}"
    if el.type in {"paragraph", "caption", "list"}:
        return text
    if el.type in {"figure", "image", "table_image"}:
        line = f"![{_alt(el)}]({el.asset_path})"
        if el.description_status == "done" and el.description_long:
            line += f"\n\n> 圖片摘要：{el.description_long}"
        else:
            line += "\n\n> 圖片描述：尚未產生，等待 VLM enrichment。"
        return line
    if el.type == "table":
        return text
    if el.type == "code":
        lang = (el.metadata or {}).get("language", "")
        return f"```{lang}\n{text}\n```"
    return text


def export_markdown(doc: Document) -> str:
    elements = sorted(doc.elements, key=lambda e: (e.page or 0, e.reading_order))
    return "\n\n".join(part for el in elements if (part := _element_markdown(el))) + "\n"
