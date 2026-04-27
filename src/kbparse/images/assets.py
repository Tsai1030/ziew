from __future__ import annotations

_KIND_DIR = {"figure": "figures", "image": "images", "table": "tables", "table_image": "tables"}
_KIND_TOKEN = {"figure": "fig", "image": "img", "table": "table", "table_image": "table"}


def make_asset_path(page: int, kind: str, index: int, ext: str = "png") -> str:
    folder = _KIND_DIR.get(kind, f"{kind}s")
    token = _KIND_TOKEN.get(kind, kind)
    return f"assets/{folder}/p{page:04d}_{token}{index:03d}.{ext.lstrip('.')}"


def make_page_image_path(page: int, ext: str = "png") -> str:
    return f"parse_artifacts/pages/page_{page:04d}.{ext.lstrip('.')}"
