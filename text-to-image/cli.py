from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tti")
    subparsers = parser.add_subparsers(dest="command", required=True)

    encrypt_parser = subparsers.add_parser("encrypt")
    encrypt_parser.add_argument("--input", required=True)
    encrypt_parser.add_argument("--output-dir", required=True)
    encrypt_parser.add_argument("--mode", type=int, default=0)

    decrypt_parser = subparsers.add_parser("decrypt")
    decrypt_parser.add_argument("--input", required=True)
    decrypt_parser.add_argument("--output-dir", required=True)

    subparsers.add_parser("inspect")
    subparsers.add_parser("verify")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    target = base / args.command / f"{args.command}.py"
    command = [sys.executable, str(target), *sys.argv[2:]]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())