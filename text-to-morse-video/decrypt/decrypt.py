"""Full decrypt pipeline for WAV/jumbled inputs.

This script supports:
- removing the loop overlay (using `RANDOM_WORD_ON_LOOP`),
- decoding WAV -> jumbled text,
- reversing the jumble to obtain AES HEX,
- AES-decrypting the HEX to recover plaintext.

It accepts a single file or a directory and supports two modes, matching the
encrypt pipeline: mode 0 (combine outputs) and mode 1 (per-file outputs).
"""
from pathlib import Path
import argparse
import math
import struct
import sys

# ensure local directory and project root import correctly
base = Path(__file__).resolve().parent
pipeline_root = base.parent
project_root = base.parent.parent
if str(base) not in sys.path:
    sys.path.insert(0, str(base))
if str(pipeline_root) not in sys.path:
    sys.path.insert(0, str(pipeline_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.ansi import success, error, info, color
from utils.env import read_env
from utils.aes import AESUtils
from payload import restore_payload

import remove_loop
import wav_to_jumbled
import rev_jumble
import string


def struct_unpack_samples(pcm_bytes: bytes):
    if not pcm_bytes:
        return []
    return struct.unpack("<{}h".format(len(pcm_bytes) // 2), pcm_bytes)


def clamp_int(x: int) -> int:
    if x > 32767:
        return 32767
    if x < -32768:
        return -32768
    return x


def process_wav(wav_path: Path, env: dict, overrides: dict) -> str:
    """Process a single WAV file and return recovered plaintext."""
    samples, fr = remove_loop.read_wav_mono(wav_path)

    dot_ms = int(overrides.get("dot_ms") or env.get("MORSE_DOT_MS", "80"))
    freq = int(overrides.get("freq") or env.get("MORSE_TONE_FREQ", "750"))
    loop_word = overrides.get("loop_word") or env.get("RANDOM_WORD_ON_LOOP", "")
    loop_volume = float(overrides.get("loop_volume") or env.get("MORSE_LOOP_VOLUME", "0.5"))

    if loop_word:
        morse = remove_loop.text_to_morse(loop_word)
        loop_pcm = remove_loop.synthesize_morse_pcm(morse, dot_ms=dot_ms, freq=freq, volume=1.0, sample_rate=fr)
        loop_samples = list(struct_unpack_samples(loop_pcm))
        if loop_samples:
            repeats = math.ceil(len(samples) / len(loop_samples))
            loop_full = (loop_samples * repeats)[: len(samples)]
        else:
            loop_full = [0] * len(samples)
        cleaned = [clamp_int(int(samples[i] - loop_full[i] * loop_volume)) for i in range(len(samples))]
    else:
        cleaned = samples

    # Decode cleaned samples into jumbled text
    runs = wav_to_jumbled.detect_runs(cleaned, fr)
    tokens = wav_to_jumbled.runs_to_morse(runs, dot_s=dot_ms / 1000.0)
    jumbled_text = wav_to_jumbled.morse_tokens_to_text(tokens)

    # Filter for hex alphanumeric characters
    jumbled_concat = ''.join(ch for ch in jumbled_text if ch in string.hexdigits)

    jump = int(overrides.get("jump") or env.get("CHARACTERS_JUMP_LENGTH", "5"))
    encrypted_hex = rev_jumble.dejumble(jumbled_concat, jump)

    key = overrides.get("key") or env.get("AES_ENCRYPT_KEY")
    iv = overrides.get("iv") or env.get("AES_INITIAL_VECTOR")
    if not key or not iv:
        raise ValueError("AES key/iv required in env or overrides")

    aes = AESUtils(key=key, iv=iv)
    plaintext = aes.decrypt(encrypted_hex)
    return plaintext


def main():
    parser = argparse.ArgumentParser(description="Full decrypt pipeline from WAV or jumbled files")
    parser.add_argument("--input", type=Path, required=True, help="Input file or directory (WAV files)")
    parser.add_argument("--mode", type=int, choices=[0, 1], default=0, help="0: club to single output; 1: per-file outputs")
    parser.add_argument("--output-dir", type=Path, default=Path("decrypted_output"), help="Output directory")
    parser.add_argument("--jump", type=int, help="Override CHARACTERS_JUMP_LENGTH")
    parser.add_argument("--dot-ms", type=int, help="Override MORSE_DOT_MS")
    parser.add_argument("--freq", type=int, help="Override MORSE_TONE_FREQ")
    parser.add_argument("--loop-word", type=str, help="Override RANDOM_WORD_ON_LOOP")
    parser.add_argument("--loop-volume", type=float, help="Override MORSE_LOOP_VOLUME")
    parser.add_argument("--key", type=str, help="Override AES key")
    parser.add_argument("--iv", type=str, help="Override AES IV")

    args = parser.parse_args()
    env = read_env(base.parent / ".env")

    inp = args.input
    files = []
    if inp.is_dir():
        files = sorted([p for p in inp.glob('*.wav')])
    elif inp.is_file():
        files = [inp]
    else:
        print(error(f"Input not found: {inp}"))
        raise SystemExit(1)

    out_dir = args.output_dir if args.output_dir.is_absolute() else Path.cwd() / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    overrides = {
        "jump": args.jump,
        "dot_ms": args.dot_ms,
        "freq": args.freq,
        "loop_word": args.loop_word,
        "loop_volume": args.loop_volume,
        "key": args.key,
        "iv": args.iv,
    }

    results = []
    for i, f in enumerate(files, start=1):
        print(info(f"Processing {f} ({i}/{len(files)})"))
        try:
            plaintext = process_wav(f, env, overrides)
        except Exception as e:
            print(error(f"Failed processing {f}: {e}"))
            continue

        if len(files) == 1 and args.mode == 0:
            target_dir = out_dir
        else:
            target_dir = out_dir / f.stem

        restored = restore_payload(plaintext, target_dir)
        if len(restored) == 1:
            print(success(f"Restored file to {color(str(restored[0]), fg='bright_green')}"))
        else:
            print(success(f"Restored {len(restored)} file(s) under {color(str(target_dir), fg='bright_green')}"))

        results.append(plaintext)


if __name__ == '__main__':
    main()
