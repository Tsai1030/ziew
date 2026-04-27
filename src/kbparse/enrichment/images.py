from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
from pathlib import Path

from kbparse.models import Document
from kbparse.providers.base import VLMProvider

PROMPT_VERSION = "image-description-v1"


def enrich_images(doc: Document, provider: VLMProvider, asset_root: Path | str | None = None) -> Document:
    updated = deepcopy(doc)
    for el in updated.elements:
        if el.type not in {"figure", "image", "table_image"}:
            continue
        try:
            image_path = _resolve_asset_path(el.asset_path, asset_root)
            result = provider.describe_image(
                image_path=image_path,
                prompt="Describe the image for a company knowledge base.",
                context={
                    "caption_nearby": el.caption_nearby,
                    "page": el.page,
                    "section_path": el.section_path,
                    "source_asset_path": el.asset_path,
                    "element_type": el.type,
                },
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
                "visual_category": result.get("visual_category"),
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


def _resolve_asset_path(asset_path: str | None, asset_root: Path | str | None) -> str:
    if not asset_path:
        return ""
    path = Path(asset_path)
    if path.is_absolute() or asset_root is None:
        return str(path)
    return str(Path(asset_root) / path)
