from __future__ import annotations

from typing import Protocol


class VLMProvider(Protocol):
    name: str
    model: str

    def describe_image(self, image_path: str, prompt: str, context: dict) -> dict:
        ...
