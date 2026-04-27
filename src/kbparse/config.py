from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    vlm_provider: str = "mock"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    local_vlm_endpoint: str = "http://localhost:8000/v1/chat/completions"


def _clean_key(value: str | None) -> str | None:
    if not value or value.strip() in {"***", ""}:
        return None
    return value


def load_config() -> Config:
    load_dotenv()
    return Config(
        vlm_provider=os.getenv("VLM_PROVIDER", "mock") or "mock",
        openai_api_key=_clean_key(os.getenv("OPENAI_API_KEY")),
        gemini_api_key=_clean_key(os.getenv("GEMINI_API_KEY")),
        local_vlm_endpoint=os.getenv("LOCAL_VLM_ENDPOINT", "http://localhost:8000/v1/chat/completions"),
    )
