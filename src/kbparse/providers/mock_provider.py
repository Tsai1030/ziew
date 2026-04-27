from __future__ import annotations


class MockVLMProvider:
    name = "mock"
    model = "mock-vlm-0.1"

    def describe_image(self, image_path: str, prompt: str, context: dict) -> dict:
        caption = context.get("caption_nearby") or context.get("alt") or "Mock image description"
        return {
            "alt_text_short": caption,
            "description_long": f"{caption}：這是 mock provider 產生的 deterministic 圖片摘要。",
            "confidence": 1.0,
            "needs_human_review": False,
        }
