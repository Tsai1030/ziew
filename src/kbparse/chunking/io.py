from __future__ import annotations

import json
from pathlib import Path
from kbparse.models import Chunk


def write_chunks_jsonl(chunks: list[Chunk], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.model_dump_json() + "\n")


def read_chunks_jsonl(path: str | Path) -> list[Chunk]:
    if not Path(path).exists():
        return []
    return [Chunk.model_validate(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
