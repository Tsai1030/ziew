import base64
import json

import pytest

from kbparse.providers.openai_compatible_provider import OpenAICompatibleVLMProvider


def test_openai_compatible_provider_sends_image_and_parses_structured_json(tmp_path):
    image = tmp_path / "figure.png"
    image.write_bytes(b"fake-png-bytes")
    captured = {}

    def fake_post(url, headers, payload, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "alt_text_short": "Transformer 架構圖",
                                "description_long": "此圖說明 encoder 與 decoder 的注意力流程。",
                                "visual_category": "architecture_diagram",
                                "confidence": 0.82,
                                "needs_human_review": False,
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }

    provider = OpenAICompatibleVLMProvider(
        api_key="test-key",
        base_url="https://api.example.test/v1",
        model="vision-model",
        http_post=fake_post,
    )

    result = provider.describe_image(
        image_path=str(image),
        prompt="describe",
        context={"caption_nearby": "Figure 1: Transformer", "page": 3},
    )

    assert captured["url"] == "https://api.example.test/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    message_content = captured["payload"]["messages"][0]["content"]
    assert any(part.get("type") == "text" and "Figure 1: Transformer" in part.get("text", "") for part in message_content)
    image_url = next(part["image_url"]["url"] for part in message_content if part.get("type") == "image_url")
    assert image_url == "data:image/png;base64," + base64.b64encode(b"fake-png-bytes").decode("ascii")
    assert result["alt_text_short"] == "Transformer 架構圖"
    assert result["description_long"].startswith("此圖說明")
    assert result["visual_category"] == "architecture_diagram"
    assert result["confidence"] == 0.82
    assert result["needs_human_review"] is False


def test_openai_compatible_provider_requires_api_key(tmp_path):
    image = tmp_path / "figure.png"
    image.write_bytes(b"fake")
    provider = OpenAICompatibleVLMProvider(api_key="", base_url="https://api.example.test/v1", model="vision-model")

    with pytest.raises(RuntimeError, match="API key"):
        provider.describe_image(str(image), "describe", {})


def test_openai_compatible_provider_normalizes_plain_text_response(tmp_path):
    image = tmp_path / "figure.png"
    image.write_bytes(b"fake")

    def fake_post(url, headers, payload, timeout):
        return {"choices": [{"message": {"content": "這是一張流程圖，展示資料從 API 進入 worker。"}}]}

    provider = OpenAICompatibleVLMProvider(
        api_key="test-key",
        base_url="https://api.example.test/v1",
        model="vision-model",
        http_post=fake_post,
    )

    result = provider.describe_image(str(image), "describe", {})

    assert result["alt_text_short"] == "這是一張流程圖，展示資料從 API 進入 worker。"
    assert result["description_long"] == "這是一張流程圖，展示資料從 API 進入 worker。"
    assert result["confidence"] == 0.5
    assert result["needs_human_review"] is True


def test_openai_compatible_provider_accepts_fenced_json_response(tmp_path):
    image = tmp_path / "figure.png"
    image.write_bytes(b"fake")

    def fake_post(url, headers, payload, timeout):
        return {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"alt_text_short":"圖表","description_long":"此圖展示趨勢。","confidence":0.9,"needs_human_review":false}\n```'
                    }
                }
            ]
        }

    provider = OpenAICompatibleVLMProvider(
        api_key="test-key",
        base_url="https://api.example.test/v1",
        model="vision-model",
        http_post=fake_post,
    )

    result = provider.describe_image(str(image), "describe", {})

    assert result["alt_text_short"] == "圖表"
    assert result["description_long"] == "此圖展示趨勢。"
    assert result["confidence"] == 0.9
    assert result["needs_human_review"] is False
