"""Build PPM images from encrypted and jumbled file payloads.

Usage:
  - Single file: `python encrypt/encrypt.py --input path/to/file.txt --mode 1`
  - Directory: `python encrypt/encrypt.py --input path/to/dir --mode 0`
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

base = Path(__file__).resolve().parent
pipeline_root = base.parent
project_root = pipeline_root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(pipeline_root) not in sys.path:
    sys.path.insert(0, str(pipeline_root))

from utils.aes import AESUtils
from utils.ansi import color, error, info, success
from utils.env import read_env
from byte_codec import bytes_to_rgb_bytes
from header import ChunkHeader
from image_ppm import image_from_rgb_bytes, write_ppm
from manifest import encode_manifest, iter_supported_files
from encrypt.jumble import jumble


def parse_extensions(raw_value: str | None) -> tuple[str, ...]:
    value = raw_value or ".txt,.json,.csv"
    return tuple(part.strip() for part in value.split(",") if part.strip())


def resolve_aes_settings(env: dict, args: argparse.Namespace) -> tuple[str, str, str]:
    key = args.key or env.get("AES_ENCRYPT_KEY") or env.get("AES_ENCRYPT")
    iv = args.iv or env.get("AES_INITIAL_VECTOR")
    mode = env.get("DEFAULT_AES_MODE", "cbc")

    if not key or not iv:
        raise ValueError("missing AES key or IV in .env or CLI arguments")

    return key, iv, mode


def collect_files(input_path: Path, extensions: tuple[str, ...]) -> tuple[list[Path], Path]:
    if input_path.is_file():
        return [input_path], input_path.parent

    if input_path.is_dir():
        return iter_supported_files(input_path, extensions), input_path

    raise FileNotFoundError(f"input not found: {input_path}")


def render_payload_to_image(payload: bytes, width: int) -> tuple[bytes, int, int]:
    chunk_header = ChunkHeader.from_payload(payload)
    packed = chunk_header.pack() + payload
    rgb_bytes, _ = bytes_to_rgb_bytes(packed)
    image = image_from_rgb_bytes(rgb_bytes, width)
    return image.pixels, image.width, image.height


def process_payload(payload_text: str, work_dir: Path, env: dict, args: argparse.Namespace) -> Path:
    key, iv, mode = resolve_aes_settings(env, args)
    aes = AESUtils(key=key, iv=iv, mode=mode)
    encrypted_hex = aes.encrypt(payload_text)
    (work_dir / "encrypted.txt").write_text(encrypted_hex, encoding="utf-8")

    jump = args.jump or int(env.get("CHARACTERS_JUMP_LENGTH", "5"))
    groups = jumble(encrypted_hex, jump)
    (work_dir / "jumbled.txt").write_text("\n".join(groups), encoding="utf-8")
    jumbled_bytes = "".join(groups).encode("ascii")

    width = args.width or int(env.get("TTI_IMAGE_WIDTH", "256"))
    pixels, image_width, image_height = render_payload_to_image(jumbled_bytes, width)
    image_path = work_dir / "final.ppm"
    write_ppm(image_path, image_from_rgb_bytes(pixels, image_width))

    metadata = (
        f"width={image_width}\n"
        f"height={image_height}\n"
        f"jump={jump}\n"
        f"payload_bytes={len(jumbled_bytes)}\n"
    )
    (work_dir / "image_info.txt").write_text(metadata, encoding="utf-8")
    return image_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AES -> jumble -> image pipeline")
    parser.add_argument("--input", type=Path, required=True, help="Input file or directory")
    parser.add_argument("--mode", type=int, choices=[0, 1], default=0, help="0: combine into one image; 1: one image per file")
    parser.add_argument("--output-dir", type=Path, default=Path("encrypted_output"), help="Output directory")
    parser.add_argument("--key", type=str, help="Override AES key")
    parser.add_argument("--iv", type=str, help="Override AES IV")
    parser.add_argument("--jump", type=int, help="Override CHARACTERS_JUMP_LENGTH")
    parser.add_argument("--width", type=int, help="Override TTI_IMAGE_WIDTH")

    args = parser.parse_args()
    env = read_env(pipeline_root / ".env")
    extensions = parse_extensions(env.get("TTI_SUPPORTED_EXTENSIONS") or env.get("TTI_SUPPORTED_EXTENSISONS"))

    try:
        files, root = collect_files(args.input, extensions)
    except FileNotFoundError as exc:
        print(error(str(exc)))
        return 1

    if not files:
        print(info("No supported files found."))
        return 0

    output_dir = args.output_dir if args.output_dir.is_absolute() else base / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == 0:
        print(info(f"Building one manifest from {len(files)} file(s)..."))
        payload_text = encode_manifest(files, root, mode=0).decode("utf-8")
        image_path = process_payload(payload_text, output_dir, env, args)
        print(success(f"Wrote image output to {color(str(image_path), fg='bright_green')}"))
        return 0

    for index, file_path in enumerate(files, start=1):
        work_dir = output_dir / file_path.stem
        work_dir.mkdir(parents=True, exist_ok=True)
        print(info(f"Processing {file_path} ({index}/{len(files)})"))
        payload_text = encode_manifest([file_path], file_path.parent, mode=1).decode("utf-8")
        image_path = process_payload(payload_text, work_dir, env, args)
        print(success(f"Wrote image output to {color(str(image_path), fg='bright_green')}"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())