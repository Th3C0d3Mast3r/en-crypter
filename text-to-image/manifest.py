from __future__ import annotations

from dataclasses import dataclass, asdict
import base64
import hashlib
import json
from pathlib import Path


@dataclass(slots=True)
class ManifestEntry:
    relative_path: str
    size: int
    sha256: str
    content_b64: str


def iter_supported_files(root: Path, extensions: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for extension in extensions:
        paths.extend(sorted(root.rglob(f"*{extension}")))
    return paths


def build_manifest_entry(path: Path, root: Path) -> ManifestEntry:
    content = path.read_bytes()
    return ManifestEntry(
        relative_path=str(path.relative_to(root)),
        size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        content_b64=base64.b64encode(content).decode("ascii"),
    )


def encode_manifest(paths: list[Path], root: Path, *, mode: int) -> bytes:
    payload = {
        "kind": "text-to-image",
        "format_version": 1,
        "mode": mode,
        "file_count": len(paths),
        "files": [asdict(build_manifest_entry(path, root)) for path in paths],
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def decode_manifest(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))


def restore_manifest(data: bytes, output_dir: Path) -> list[Path]:
    document = decode_manifest(data)
    restored: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in document.get("files", []):
        rel_path = Path(str(item["relative_path"]))
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"unsafe manifest path: {rel_path}")

        content = base64.b64decode(item["content_b64"])
        if len(content) != int(item["size"]):
            raise ValueError(f"size mismatch for {rel_path}")

        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != item["sha256"]:
            raise ValueError(f"sha256 mismatch for {rel_path}")

        target = output_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        restored.append(target)

    return restored