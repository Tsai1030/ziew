from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ElementType = Literal["paragraph", "heading", "list", "table", "figure", "image", "table_image", "code", "caption"]
ChunkType = Literal["text", "visual", "table", "code", "evidence_unit"]

_IMAGE_PATH_RE = re.compile(r"(assets/|\.(png|jpg|jpeg|webp)\b)", re.IGNORECASE)


class Source(BaseModel):
    path: str
    sha256: str | None = None
    mime_type: str = "application/pdf"


class Page(BaseModel):
    page_num: int
    width: float
    height: float
    page_image_path: str | None = None


class ParserInfo(BaseModel):
    name: str
    version: str = "0.1.0"


class Element(BaseModel):
    element_id: str
    type: ElementType
    page: int | None = None
    bbox: list[float] | None = None
    reading_order: int
    section_path: list[str] = Field(default_factory=list)
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    asset_path: str | None = None
    markdown: str | None = None
    caption_nearby: str | None = None
    description_status: Literal["pending", "done", "failed"] | None = None
    alt_text_short: str | None = None
    description_long: str | None = None
    source: dict[str, Any] | None = None
    enrichment: dict[str, Any] | None = None

    @field_validator("bbox")
    @classmethod
    def bbox_len_four(cls, value: list[float] | None) -> list[float] | None:
        if value is not None and len(value) != 4:
            raise ValueError("bbox must contain exactly four numbers")
        return value

    @field_validator("asset_path")
    @classmethod
    def asset_path_relative(cls, value: str | None) -> str | None:
        if value is None:
            return value
        p = PurePosixPath(value.replace("\\", "/"))
        if p.is_absolute() or re.match(r"^[A-Za-z]:", value):
            raise ValueError("asset_path must be relative")
        return str(p)


class Document(BaseModel):
    schema_version: str = "0.1.0"
    doc_id: str
    source: Source
    pages: list[Page] = Field(default_factory=list)
    elements: list[Element] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parser: ParserInfo


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    chunk_type: ChunkType
    text: str
    text_for_embedding: str
    markdown: str = ""
    asset_path: str | None = None
    related_assets: list[str] = Field(default_factory=list)
    page: int | None = None
    page_range: list[int] | None = None
    bbox: list[float] | None = None
    source_element_ids: list[str]
    section_path: list[str] = Field(default_factory=list)
    do_not_split: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("bbox")
    @classmethod
    def chunk_bbox_len_four(cls, value: list[float] | None) -> list[float] | None:
        if value is not None and len(value) != 4:
            raise ValueError("bbox must contain exactly four numbers")
        return value

    @field_validator("asset_path")
    @classmethod
    def chunk_asset_relative(cls, value: str | None) -> str | None:
        if value and (PurePosixPath(value.replace("\\", "/")).is_absolute() or re.match(r"^[A-Za-z]:", value)):
            raise ValueError("asset_path must be relative")
        return value

    @model_validator(mode="after")
    def validate_embedding_and_visual(self) -> "Chunk":
        if _IMAGE_PATH_RE.search(self.text_for_embedding):
            raise ValueError("text_for_embedding must not contain raw image paths")
        if self.chunk_type == "visual":
            if not self.asset_path or self.page is None or self.bbox is None or not self.do_not_split:
                raise ValueError("visual chunks require asset_path, page, bbox, and do_not_split")
        if self.chunk_type in {"table", "code"} and not self.do_not_split:
            raise ValueError("table/code chunks must be atomic")
        return self
