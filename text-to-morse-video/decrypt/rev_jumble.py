from pathlib import Path
import argparse
import sys

base = Path(__file__).resolve().parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.ansi import success, error, info, color
from utils.env import read_env


def dejumble(groups: str, jump: int) -> str:
    lines = [line.strip() for line in groups.splitlines() if line.strip()]
    if len(lines) == jump:
        parts = lines
    else:
        compact = "".join(groups.split())
        parts = _split_compact_groups(compact, jump)

    out = []
    for i in range(max(len(p) for p in parts)):
        for p in parts:
            if i < len(p):
                out.append(p[i])
    return "".join(out)


def _split_compact_groups(groups: str, jump: int):
    total = len(groups)
    base = total // jump
    extras = total % jump
    parts = []
    idx = 0
    for i in range(jump):
        size = base + (1 if i < extras else 0)
        parts.append(groups[idx: idx + size])
        idx += size

    return parts


def main():
    parser = argparse.ArgumentParser(description="Reverse jumble into encrypted hex")
    parser.add_argument("--input", type=Path, default=Path("jumbled.txt"))
    parser.add_argument("--output", type=Path, default=Path("encrypted_recovered.txt"))
    parser.add_argument("--jump", type=int, help="Override CHARACTERS_JUMP_LENGTH from .env")

    args = parser.parse_args()
    base = Path(__file__).resolve().parent.parent
    env = read_env(base / ".env")
    jump = args.jump if args.jump is not None else int(env.get("CHARACTERS_JUMP_LENGTH", "5"))

    inp = args.input if args.input.is_absolute() else Path.cwd() / args.input
    if not inp.exists():
        print(error(f"Input not found: {inp}"))
        raise SystemExit(1)

    groups = inp.read_text(encoding="utf-8").strip()
    recovered = dejumble(groups, jump)
    outp = args.output if args.output.is_absolute() else Path.cwd() / args.output
    outp.write_text(recovered, encoding="utf-8")
    print(success(f"Wrote recovered hex to {color(str(outp), fg='bright_green')}"))


if __name__ == "__main__":
    main()
