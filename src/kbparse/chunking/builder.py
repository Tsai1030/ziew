from __future__ import annotations

from kbparse.exporters.markdown import _element_markdown
from kbparse.models import Chunk, Document, Element


def _flush_text(doc: Document, bucket: list[Element], chunks: list[Chunk]) -> None:
    if not bucket:
        return
    text = "\n".join(e.text or "" for e in bucket if e.text)
    if not text.strip():
        bucket.clear(); return
    first, last = bucket[0], bucket[-1]
    chunks.append(Chunk(
        chunk_id=f"{doc.doc_id}_{first.element_id}_text",
        doc_id=doc.doc_id,
        chunk_type="text",
        text=text,
        text_for_embedding=text,
        markdown="\n\n".join(_element_markdown(e) for e in bucket),
        page=first.page,
        page_range=[first.page or 0, last.page or first.page or 0],
        source_element_ids=[e.element_id for e in bucket],
        section_path=first.section_path,
    ))
    bucket.clear()


def _visual_chunk(doc: Document, el: Element) -> Chunk:
    caption = el.caption_nearby or "圖片"
    pending = "圖片描述尚未產生。" if el.description_status != "done" else (el.description_long or "")
    return Chunk(
        chunk_id=f"{doc.doc_id}_{el.element_id}",
        doc_id=doc.doc_id,
        chunk_type="visual",
        text=f"圖片：第 {el.page} 頁，{caption}。{pending}",
        text_for_embedding=f"圖片：{caption}。{pending}",
        markdown=_element_markdown(el),
        asset_path=el.asset_path,
        page=el.page,
        bbox=el.bbox,
        source_element_ids=[el.element_id],
        section_path=el.section_path,
        do_not_split=True,
    )


def _atomic_chunk(doc: Document, el: Element) -> Chunk:
    return Chunk(
        chunk_id=f"{doc.doc_id}_{el.element_id}",
        doc_id=doc.doc_id,
        chunk_type="table" if el.type == "table" else "code",
        text=el.text or "",
        text_for_embedding=el.text or "",
        markdown=_element_markdown(el),
        asset_path=el.asset_path,
        related_assets=[el.asset_path] if el.asset_path else [],
        page=el.page,
        bbox=el.bbox,
        source_element_ids=[el.element_id],
        section_path=el.section_path,
        do_not_split=True,
    )


def _evidence_units(doc: Document) -> list[Chunk]:
    chunks: list[Chunk] = []
    elements = sorted(doc.elements, key=lambda e: (e.page or 0, e.reading_order))
    by_id = {id(e): i for i, e in enumerate(elements)}
    for el in elements:
        if el.type not in {"figure", "image", "table", "code", "table_image"}:
            continue
        i = by_id[id(el)]
        nearby = [e for e in elements[max(0, i-2): min(len(elements), i+3)] if e.page == el.page and e.type in {"heading", "paragraph", "caption"}]
        texts = [t for e in nearby for t in [e.text] if t]
        if el.caption_nearby:
            texts.append(el.caption_nearby)
        if el.text and el.type in {"table", "code"}:
            texts.append(el.text)
        combined = "\n".join(dict.fromkeys(texts)) or (el.caption_nearby or el.text or "evidence")
        related = [el.asset_path] if el.asset_path else []
        chunks.append(Chunk(
            chunk_id=f"{doc.doc_id}_{el.element_id}_evidence",
            doc_id=doc.doc_id,
            chunk_type="evidence_unit",
            text=combined,
            text_for_embedding=combined,
            markdown="\n\n".join(_element_markdown(e) for e in nearby + [el]),
            related_assets=related,
            page=el.page,
            bbox=el.bbox,
            source_element_ids=[e.element_id for e in nearby] + [el.element_id],
            section_path=el.section_path,
            do_not_split=True,
        ))
    return chunks


def build_chunks(doc: Document, include_evidence_units: bool = False) -> list[Chunk]:
    chunks: list[Chunk] = []
    text_bucket: list[Element] = []
    for el in sorted(doc.elements, key=lambda e: (e.page or 0, e.reading_order)):
        if el.type in {"heading", "paragraph", "list", "caption"}:
            text_bucket.append(el)
        elif el.type in {"figure", "image", "table_image"}:
            _flush_text(doc, text_bucket, chunks)
            chunks.append(_visual_chunk(doc, el))
        elif el.type in {"table", "code"}:
            _flush_text(doc, text_bucket, chunks)
            chunks.append(_atomic_chunk(doc, el))
    _flush_text(doc, text_bucket, chunks)
    if include_evidence_units:
        chunks.extend(_evidence_units(doc))
    return chunks
