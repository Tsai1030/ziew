from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Callable
from urllib import error, request


class OpenAICompatibleVLMProvider:
    """Vision provider for OpenAI-compatible chat/completions APIs.

    Reads config from environment by default:
    - KBPARSE_VLM_API_KEY or OPENAI_API_KEY
    - KBPARSE_VLM_BASE_URL or OPENAI_BASE_URL
    - KBPARSE_VLM_MODEL or OPENAI_VISION_MODEL
    """

    name = "openai-compatible"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 60,
        http_post: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else (os.getenv("KBPARSE_VLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "")
        self.base_url = (base_url or os.getenv("KBPARSE_VLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.getenv("KBPARSE_VLM_MODEL") or os.getenv("OPENAI_VISION_MODEL") or "gpt-4o-mini"
        self.timeout = timeout
        self._http_post = http_post or _urllib_post_json

    def describe_image(self, image_path: str, prompt: str, context: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("API key is required for openai-compatible provider. Set KBPARSE_VLM_API_KEY or OPENAI_API_KEY.")
        path = Path(image_path)
        if not path.exists():
            raise RuntimeError(f"Image file does not exist: {image_path}")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _build_prompt(prompt, context)},
                        {"type": "image_url", "image_url": {"url": _data_url(path)}},
                    ],
                }
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = self._http_post(f"{self.base_url}/chat/completions", headers, payload, self.timeout)
        content = _message_content(response)
        return _normalize_result(content)


def _build_prompt(prompt: str, context: dict) -> str:
    context_lines = []
    if context.get("caption_nearby"):
        context_lines.append(f"Nearby caption: {context['caption_nearby']}")
    if context.get("page"):
        context_lines.append(f"Page: {context['page']}")
    if context.get("section_path"):
        context_lines.append(f"Section path: {' > '.join(context['section_path'])}")
    if context.get("source_asset_path"):
        context_lines.append(f"Source asset path: {context['source_asset_path']}")

    return "\n".join(
        [
            prompt,
            "Return ONLY a JSON object with keys: alt_text_short, description_long, visual_category, confidence, needs_human_review.",
            "Describe facts grounded in the image. If unsure, say so and set needs_human_review=true.",
            *context_lines,
        ]
    )


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _message_content(response: dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenAI-compatible response did not contain choices[0].message.content") from exc


def _normalize_result(content: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(content, dict):
        data = content
    else:
        text_content = _strip_json_fence(content.strip())
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError:
            text = content.strip()
            return {
                "alt_text_short": text[:120],
                "description_long": text,
                "visual_category": "unknown",
                "confidence": 0.5,
                "needs_human_review": True,
            }

    description = str(data.get("description_long") or data.get("description") or data.get("summary") or "").strip()
    alt = str(data.get("alt_text_short") or data.get("alt") or description[:120] or "圖片描述").strip()
    confidence = data.get("confidence", 0.5)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))
    return {
        "alt_text_short": alt[:160],
        "description_long": description or alt,
        "visual_category": str(data.get("visual_category") or data.get("type") or "unknown"),
        "confidence": confidence,
        "needs_human_review": bool(data.get("needs_human_review", confidence < 0.7)),
    }


def _strip_json_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _urllib_post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"OpenAI-compatible API HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI-compatible API request failed: {exc.reason}") from exc
