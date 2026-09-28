"""Recover manifest payloads from text-to-image PPM outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import zlib

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
from header import HEADER_STRUCT, unpack_header
from image_ppm import read_ppm
from manifest import restore_manifest
from decrypt.rev_jumble import reverse_jumble


def resolve_aes_settings(env: dict, args: argparse.Namespace) -> tuple[str, str, str]:
    key = args.key or env.get("AES_ENCRYPT_KEY") or env.get("AES_ENCRYPT")
    iv = args.iv or env.get("AES_INITIAL_VECTOR")
    mode = env.get("DEFAULT_AES_MODE", "cbc")
    if not key or not iv:
        raise ValueError("missing AES key or IV in .env or CLI arguments")
    return key, iv, mode


def decode_payload_from_image(image_path: Path) -> bytes:
    image = read_ppm(image_path)
    packed = image.pixels
    header = unpack_header(packed)
    payload_start = HEADER_STRUCT.size
    payload_end = payload_start + header.payload_length
    payload = packed[payload_start:payload_end]

    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    if checksum != header.checksum:
        raise ValueError(f"checksum mismatch in {image_path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Reverse image -> jumble -> AES pipeline")
    parser.add_argument("--input", type=Path, required=True, help="Input PPM image")
    parser.add_argument("--output-dir", type=Path, default=Path("decrypted_output"), help="Directory for restored files")
    parser.add_argument("--key", type=str, help="Override AES key")
    parser.add_argument("--iv", type=str, help="Override AES IV")
    parser.add_argument("--jump", type=int, help="Override CHARACTERS_JUMP_LENGTH")
    args = parser.parse_args()

    if not args.input.exists() or not args.input.is_file():
        print(error(f"input image not found: {args.input}"))
        return 1

    env = read_env(pipeline_root / ".env")
    key, iv, mode = resolve_aes_settings(env, args)
    jump = args.jump or int(env.get("CHARACTERS_JUMP_LENGTH", "5"))
    output_dir = args.output_dir if args.output_dir.is_absolute() else base / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(info(f"Reading {args.input}..."))
    jumbled_text = decode_payload_from_image(args.input).decode("ascii")
    encrypted_hex = reverse_jumble(jumbled_text, jump)
    aes = AESUtils(key=key, iv=iv, mode=mode)
    plaintext = aes.decrypt(encrypted_hex)

    restored = restore_manifest(plaintext.encode("utf-8"), output_dir)
    print(success(f"Restored {len(restored)} file(s) into {color(str(output_dir), fg='bright_green')}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())