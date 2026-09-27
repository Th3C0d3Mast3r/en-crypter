"""Remove the looping morse overlay from a mixed WAV.

This script reads `final.wav` (or any WAV with the loop mixed in), synthesizes
the loop word morse from `RANDOM_WORD_ON_LOOP` (or `--loop-word`) using the
MORSE settings in `.env`, repeats/truncates it to match the input length, and
subtracts it (scaled by `--loop-volume`) to recover the main morse audio.

Usage:
  python remove_loop.py --input final.wav --output clean.wav
"""
from pathlib import Path
import wave
import struct
import math
import argparse
import sys

# ensure local directory and project root import correctly
base = Path(__file__).resolve().parent
encrypt_dir = base.parent / "encrypt"
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(encrypt_dir) not in sys.path:
    sys.path.insert(0, str(encrypt_dir))

from utils.ansi import success, error, info, color
from utils.env import read_env
from toMorseCode import text_to_morse


def synthesize_morse_pcm(morse: str, dot_ms: int, freq: int, volume: float, sample_rate: int = 44100) -> bytes:
    dot_s = dot_ms / 1000.0
    dash_s = dot_s * 3
    intra_element_s = dot_s
    between_letters_s = dot_s * 3
    between_words_s = dot_s * 7

    amplitude = int(32767 * max(0.0, min(1.0, volume)))
    samples = []

    def tone(duration_s: float):
        n = int(sample_rate * duration_s)
        for i in range(n):
            t = i / sample_rate
            samples.append(int(amplitude * math.sin(2 * math.pi * freq * t)))

    def silence(duration_s: float):
        n = int(sample_rate * duration_s)
        for _ in range(n):
            samples.append(0)

    tokens = morse.split(" ")
    first_token = True
    for token in tokens:
        if not first_token:
            silence(between_letters_s)
        first_token = False
        if token == "/":
            silence(between_words_s)
            continue
        for i, sym in enumerate(token):
            if sym == ".":
                tone(dot_s)
            elif sym == "-":
                tone(dash_s)
            else:
                silence(intra_element_s)
            if i != len(token) - 1:
                silence(intra_element_s)

    # trailing silence buffer
    silence(between_words_s)

    return struct.pack("<{}h".format(len(samples)), *samples)


def read_wav_mono(path: Path):
    with wave.open(str(path), "rb") as wf:
        nchan = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if nchan != 1 or sampwidth != 2:
        raise ValueError("Only mono 16-bit WAV supported")
    samples = list(struct.unpack("<{}h".format(len(frames) // 2), frames))
    return samples, fr


def write_wav_mono(path: Path, samples: list, fr: int):
    data = struct.pack("<{}h".format(len(samples)), *samples)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fr)
        wf.writeframes(data)


def clamp(x: int) -> int:
    if x > 32767:
        return 32767
    if x < -32768:
        return -32768
    return x


def main():
    parser = argparse.ArgumentParser(description="Remove looping morse overlay from WAV")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--loop-word", type=str, help="Override RANDOM_WORD_ON_LOOP from .env")
    parser.add_argument("--dot-ms", type=int, help="Override MORSE_DOT_MS from .env")
    parser.add_argument("--freq", type=int, help="Override MORSE_TONE_FREQ from .env")
    parser.add_argument("--loop-volume", type=float, help="Loop volume used when mixing (0-1)")

    args = parser.parse_args()
    env = read_env(base.parent / ".env")
    loop_word = args.loop_word if args.loop_word is not None else env.get("RANDOM_WORD_ON_LOOP", "")
    if not loop_word:
        print(error("No loop word provided via --loop-word or RANDOM_WORD_ON_LOOP in .env"))
        raise SystemExit(1)

    dot_ms = int(args.dot_ms if args.dot_ms is not None else env.get("MORSE_DOT_MS", "80"))
    freq = int(args.freq if args.freq is not None else env.get("MORSE_TONE_FREQ", "750"))
    loop_volume = float(args.loop_volume if args.loop_volume is not None else env.get("MORSE_LOOP_VOLUME", "0.5"))

    inp = args.input
    if not inp.exists():
        print(error(f"Input WAV not found: {inp}"))
        raise SystemExit(1)

    samples, fr = read_wav_mono(inp)
    total_bytes = len(samples) * 2

    # synthesize loop morse pcm
    morse = text_to_morse(loop_word)
    loop_pcm = synthesize_morse_pcm(morse, dot_ms=dot_ms, freq=freq, volume=1.0, sample_rate=fr)
    loop_samples = list(struct.unpack("<{}h".format(len(loop_pcm) // 2), loop_pcm))

    # repeat/truncate loop samples to match length
    if len(loop_samples) == 0:
        print(info("Loop morse synthesized to zero length; nothing to remove."))
        write_wav_mono(args.output, samples, fr)
        print(success(f"Wrote {color(str(args.output), fg='bright_green')}"))
        return

    repeats = math.ceil(len(samples) / len(loop_samples))
    loop_full = (loop_samples * repeats)[: len(samples)]

    # subtract scaled loop from mixed
    out = [clamp(int(s - loop_full[i] * loop_volume)) for i, s in enumerate(samples)]

    write_wav_mono(args.output, out, fr)
    print(success(f"Wrote cleaned WAV to {color(str(args.output), fg='bright_green')}"))


if __name__ == "__main__":
    main()
