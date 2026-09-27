from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Iterable


PAYLOAD_KIND = "text-to-morse-video"
PAYLOAD_VERSION = 1


def _to_posix(path: Path) -> str:
    return path.as_posix()


def build_payload(paths: Iterable[Path], root: Path) -> str:
    root = root.resolve()
    items = []
    for path in sorted({p.resolve() for p in paths}):
        data = path.read_bytes()
        rel_path = _to_posix(path.relative_to(root))
        items.append(
            {
                "path": rel_path,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "content_b64": base64.b64encode(data).decode("ascii"),
            }
        )

    document = {
        "kind": PAYLOAD_KIND,
        "version": PAYLOAD_VERSION,
        "items": items,
    }
    return json.dumps(document, ensure_ascii=True, separators=(",", ":"))


def parse_payload(text: str) -> dict | None:
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(document, dict):
        return None
    if document.get("kind") != PAYLOAD_KIND:
        return None
    if document.get("version") != PAYLOAD_VERSION:
        raise ValueError(f"Unsupported payload version: {document.get('version')}")

    items = document.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Payload is missing file items")

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Payload item must be an object")
        for key in ("path", "sha256", "size", "content_b64"):
            if key not in item:
                raise ValueError(f"Payload item missing {key}")

    return document


def restore_payload(text: str, output_dir: Path) -> list[Path]:
    document = parse_payload(text)
    output_dir.mkdir(parents=True, exist_ok=True)

    if document is None:
        target = output_dir / "recovered.txt"
        target.write_text(text, encoding="utf-8")
        return [target]

    restored = []
    for item in document["items"]:
        rel_path = Path(str(item["path"]))
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"Unsafe payload path: {rel_path}")

        data = base64.b64decode(item["content_b64"])
        expected_hash = str(item["sha256"])
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Integrity check failed for {rel_path}")
        if len(data) != int(item["size"]):
            raise ValueError(f"Size mismatch for {rel_path}")

        target = output_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        restored.append(target)

    return restored