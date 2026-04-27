from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy

from kbparse.models import Document
from kbparse.providers.base import VLMProvider

PROMPT_VERSION = "image-description-v1"


def enrich_images(doc: Document, provider: VLMProvider) -> Document:
    updated = deepcopy(doc)
    for el in updated.elements:
        if el.type not in {"figure", "image", "table_image"}:
            continue
        try:
            result = provider.describe_image(
                image_path=el.asset_path or "",
                prompt="Describe the image for a company knowledge base.",
                context={"caption_nearby": el.caption_nearby, "page": el.page, "section_path": el.section_path},
            )
            el.description_status = "done"
            el.alt_text_short = result.get("alt_text_short")
            el.description_long = result.get("description_long")
            el.enrichment = {
                "provider": provider.name,
                "model": provider.model,
                "prompt_version": PROMPT_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "confidence": result.get("confidence", 0.0),
                "needs_human_review": result.get("needs_human_review", True),
            }
        except Exception as exc:
            el.description_status = "failed"
            el.enrichment = {
                "provider": getattr(provider, "name", "unknown"),
                "model": getattr(provider, "model", "unknown"),
                "prompt_version": PROMPT_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.0,
                "needs_human_review": True,
                "error": str(exc)[:500],
            }
    return updated
