"""Pipeline runner to produce final morse audio from files or a directory.

Usage:
  - Single file: `python encrypt.py --input path/to/file.txt --mode 1`
  - Directory: `python encrypt.py --input path/to/dir --mode 0`

Modes:
  - 0: club multiple files into a single final audio (`encrypted_output/final.*`)
  - 1: each file produces its own final audio under `encrypted_output/<name>/final.*`

Defaults are read from the local `.env` file unless overridden by CLI flags.
All terminal output uses the shared `utils` ANSI helpers.
"""
from pathlib import Path
import sys
import time
import argparse
import os
import math

# ensure local modules and project root import correctly
base = Path(__file__).resolve().parent
pipeline_root = base.parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(pipeline_root) not in sys.path:
    sys.path.insert(0, str(pipeline_root))
if str(base) not in sys.path:
    sys.path.insert(0, str(base))

from utils.ansi import success, error, info, color
from utils.env import read_env
from payload import build_payload

from aesConversion import AESUtils
from jumbleEncrypted import jumble
from toMorseCode import text_to_morse, synthesize_morse, write_wav, try_convert_to_mp3


def mix_pcm(pcm_a: bytes, pcm_b: bytes, volume_a: float = 1.0, volume_b: float = 0.5) -> bytes:
    # assume 16-bit little-endian signed PCM
    import struct
    n = min(len(pcm_a), len(pcm_b)) // 2
    fmt = "<{}h".format(n)
    a_samples = struct.unpack(fmt, pcm_a[: n * 2])
    b_samples = struct.unpack(fmt, pcm_b[: n * 2])
    out = []
    for i in range(n):
        s = int(a_samples[i] * volume_a + b_samples[i] * volume_b)
        if s > 32767:
            s = 32767
        if s < -32768:
            s = -32768
        out.append(s)
    return struct.pack(fmt, *out) + (pcm_a[n * 2 :] if len(pcm_a) > n * 2 else b"")


def process_text(text: str, work_dir: Path, env: dict, overrides: dict) -> bytes:
    """Process normalized text through AES -> jumble -> morse synthesis and return mixed PCM bytes."""
    # AES encrypt
    key = overrides.get("key") or env.get("AES_ENCRYPT_KEY")
    iv = overrides.get("iv") or env.get("AES_INITIAL_VECTOR")
    mode = overrides.get("mode") or env.get("DEFAULT_AES_MODE")
    aes = AESUtils(key=key, iv=iv, mode=mode)
    encrypted_hex = aes.encrypt(text)

    # write encrypted.txt
    (work_dir / "encrypted.txt").write_text(encrypted_hex, encoding="utf-8")

    # jumble
    jump = int(overrides.get("jump") or env.get("CHARACTERS_JUMP_LENGTH", "5"))
    groups = jumble(encrypted_hex, jump)
    jumbled = "".join(groups)
    (work_dir / "jumbled.txt").write_text("\n".join(groups), encoding="utf-8")

    # synthesize main morse pcm
    dot_ms = int(overrides.get("dot_ms") or env.get("MORSE_DOT_MS", "80"))
    freq = int(overrides.get("freq") or env.get("MORSE_TONE_FREQ", "750"))
    volume = float(overrides.get("main_volume") or env.get("MORSE_MAIN_VOLUME", "1.0"))
    morse = text_to_morse(jumbled)
    pcm_main = synthesize_morse(morse, dot_ms=dot_ms, freq=freq, volume=volume)

    # prepare loop
    loop_word = overrides.get("loop_word") or env.get("RANDOM_WORD_ON_LOOP", "")
    loop_volume = float(overrides.get("loop_volume") or env.get("MORSE_LOOP_VOLUME", "0.5"))
    if loop_word:
        loop_morse = text_to_morse(loop_word)
        pcm_loop_single = synthesize_morse(loop_morse, dot_ms=dot_ms, freq=freq, volume=1.0)
        if len(pcm_loop_single) == 0:
            pcm_loop = b""
        else:
            repeats = math.ceil(len(pcm_main) / len(pcm_loop_single))
            pcm_loop = (pcm_loop_single * repeats)[: len(pcm_main)]
        mixed = mix_pcm(pcm_main, pcm_loop, volume_a=1.0, volume_b=loop_volume)
    else:
        mixed = pcm_main

    return mixed


def build_file_payload(path: Path) -> str:
    return build_payload([path], path.parent)


def build_directory_payload(paths: list[Path], root: Path) -> str:
    return build_payload(paths, root)


def main():
    parser = argparse.ArgumentParser(description="Run full encrypt -> morse pipeline")
    parser.add_argument("--input", type=Path, required=True, help="Input file or directory")
    parser.add_argument("--mode", type=int, choices=[0, 1], default=0, help="0: club to single wav; 1: each file its own wav")
    parser.add_argument("--output-dir", type=Path, default=Path("encrypted_output"), help="Output directory")
    # overrides
    parser.add_argument("--key", type=str, help="Override AES key")
    parser.add_argument("--iv", type=str, help="Override AES IV")
    parser.add_argument("--jump", type=int, help="Override CHARACTERS_JUMP_LENGTH")
    parser.add_argument("--dot-ms", type=int, help="Override MORSE_DOT_MS")
    parser.add_argument("--freq", type=int, help="Override MORSE_TONE_FREQ")
    parser.add_argument("--loop-word", type=str, help="Override RANDOM_WORD_ON_LOOP")
    parser.add_argument("--loop-volume", type=float, help="Override MORSE_LOOP_VOLUME")
    parser.add_argument("--main-volume", type=float, help="Override MORSE_MAIN_VOLUME")
    parser.add_argument("--format", choices=["mp3", "wav"], help="Output format")

    args = parser.parse_args()

    env = read_env(base.parent / ".env")
    out_dir = args.output_dir if args.output_dir.is_absolute() else base / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    overrides = {
        "key": args.key,
        "iv": args.iv,
        "jump": args.jump,
        "dot_ms": args.dot_ms,
        "freq": args.freq,
        "loop_word": args.loop_word,
        "loop_volume": args.loop_volume,
        "main_volume": args.main_volume,
    }

    inp = args.input
    files = []
    if inp.is_dir():
        for ext in ("*.txt", "*.csv", "*.json"):  # supported
            files.extend(sorted(inp.rglob(ext)))
    elif inp.is_file():
        files = [inp]
    else:
        print(error(f"Input not found: {inp}"))
        raise SystemExit(1)

    if not files:
        print(info("No input files found."))
        return

    start = time.time()

    if args.mode == 0:
        payload = build_directory_payload(files, inp if inp.is_dir() else inp.parent)
        print(info(f"Clubbing {len(files)} file(s) into single output payload..."))
        pcm = process_text(payload, out_dir, env, overrides)
        
        final_path = out_dir / "final.wav"
        write_wav(final_path, pcm)
        out_format = args.format or env.get("MORSE_OUTPUT_FORMAT", "mp3")
        if out_format == "mp3":
            ok = try_convert_to_mp3(final_path, out_dir / "final.mp3")
            if ok:
                final_path.unlink(missing_ok=True)
        print(success(f"Wrote final output to {color(str(out_dir), fg='bright_green')}"))
    else:
        # Mode 1: each file produces its own output directory and audio
        for i, f in enumerate(files, start=1):
            t0 = time.time()
            name = f.stem
            work_dir = out_dir / name
            work_dir.mkdir(parents=True, exist_ok=True)
            print(info(f"Processing {f} ({i}/{len(files)})"))
            payload = build_file_payload(f)
            pcm = process_text(payload, work_dir, env, overrides)

            elapsed = time.time() - t0
            avg = (time.time() - start) / i
            remaining = avg * (len(files) - i)
            print(info(f"Done {name} in {elapsed:.1f}s — ETA {remaining:.1f}s"))

            target = work_dir / "final.wav"
            write_wav(target, pcm)
            out_format = args.format or env.get("MORSE_OUTPUT_FORMAT", "mp3")
            if out_format == "mp3":
                ok = try_convert_to_mp3(target, work_dir / "final.mp3")
                if ok:
                    target.unlink(missing_ok=True)
            print(success(f"Wrote output for {name} to {color(str(work_dir), fg='bright_green')}"))


if __name__ == "__main__":
    main()
