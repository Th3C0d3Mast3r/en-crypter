"""Jumble encrypted output based on CHARACTERS_JUMP_LENGTH from .env.

Reads `encrypted.txt` (hex output from AES), groups characters by index % jump length,
and writes `jumbled.txt` listing groups in order 0..(jump-1). This is reversible by
reading groups and interleaving them back.
"""
from pathlib import Path
import os
import sys
import argparse
from typing import List

base = Path(__file__).resolve().parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.ansi import success, error, info, color
from utils.env import read_env



def jumble(encrypted_hex: str, jump: int) -> List[str]:
    groups = ["" for _ in range(jump)]
    for idx, ch in enumerate(encrypted_hex):
        groups[idx % jump] += ch
    return groups


def main():
    parser = argparse.ArgumentParser(description="Jumble AES hex output into groups")
    parser.add_argument("--input-file", type=Path, help="Path to encrypted hex file", default=Path("encrypted.txt"))
    parser.add_argument("--output-file", type=Path, help="Path to write jumbled groups", default=Path("jumbled.txt"))
    parser.add_argument("--jump", type=int, help="Override CHARACTERS_JUMP_LENGTH", default=None)

    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    env = read_env(base / ".env")
    jump = int(env.get("CHARACTERS_JUMP_LENGTH", "5")) if args.jump is None else args.jump

    src = args.input_file if args.input_file.is_absolute() else base / args.input_file
    if not src.exists():
        print(error(f"encrypted file not found: {src}"))
        raise SystemExit(1)

    encrypted = src.read_text(encoding="utf-8").strip()
    groups = jumble(encrypted, jump)

    out = args.output_file if args.output_file.is_absolute() else base / args.output_file
    out.write_text("".join(groups), encoding="utf-8")
    print(success(f"Wrote jumbled output to {color(str(out), fg='bright_green')} (jump={jump})"))


if __name__ == "__main__":
    main()
