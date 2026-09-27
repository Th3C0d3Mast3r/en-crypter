import argparse
import sys
from pathlib import Path
import json
import pandas as pd

base = Path(__file__).resolve().parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.ansi import (
    success,
    error,
    warning,
    info,
    color,
    strip_ansi,
    supports_color,
    bold,
    underline,
    dim,
)
from utils.env import read_env

env = read_env(base.parent / ".env")


def load_data(input_file: Path):
    """Load supported input formats into a common representation."""

    extension = input_file.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(input_file)

    elif extension == ".json":
        with open(input_file, "r", encoding="utf-8") as f:
            return json.load(f)

    elif extension in {".txt", ".text"}:
        return input_file.read_text(encoding="utf-8")

    else:
        raise ValueError(f"Unsupported file format: {extension}")


def normalize(data):
    """Convert loaded data into readable text."""

    if isinstance(data, pd.DataFrame):
        return data.to_string(index=False)

    elif isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, ensure_ascii=False)

    elif isinstance(data, str):
        return data

    else:
        return str(data)


def main():
    parser = argparse.ArgumentParser(
        description="Convert data files into readable text."
    )

    parser.add_argument(
        "--input-file",
        type=Path,
        required=True,
        help="Path to the input data file"
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("output.txt"),
        help="Path to the output text file"
    )

    args = parser.parse_args()

    try:
        data = load_data(args.input_file)
        text = normalize(data)

        args.output_file.write_text(text, encoding="utf-8")

        src = color(str(args.input_file), fg="bright_blue")
        dst = color(str(args.output_file), fg="bright_green")
        print(success(f"Converted {src} -> {dst}"))

    except Exception as e:
        msg = color(str(e), fg="bright_red")
        print(error(f"Error: {msg}"))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
