"""Convert a cleaned morse WAV into jumbled text (hex string reconstruction).

This script performs a simple energy-based segmentation to detect tones and
silences, classifies durations into dots/dashes and gaps, reconstructs Morse
tokens and maps them back to characters. It expects mono 16-bit WAV input.
"""
from pathlib import Path
import wave
import struct
import argparse
import math
import sys

# ensure local directory and project root import correctly
base = Path(__file__).resolve().parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.ansi import success, error, info, color
from utils.env import read_env


# Reverse MORSE map
MORSE_MAP = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
}


def read_wav_samples(path: Path):
    with wave.open(str(path), "rb") as wf:
        nchan = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if nchan != 1 or sampwidth != 2:
        raise ValueError("Only mono 16-bit WAV supported")
    samples = list(struct.unpack("<{}h".format(len(frames) // 2), frames))
    return samples, fr


def detect_runs(samples, fr, threshold=None):
    # compute absolute values
    abs_s = [abs(s) for s in samples]
    maxv = max(abs_s) if abs_s else 0
    if threshold is None:
        threshold = max(100, int(maxv * 0.15))

    runs = []  # list of (is_tone:bool, duration_s)
    i = 0
    n = len(samples)
    while i < n:
        is_tone = abs_s[i] > threshold
        j = i
        while j < n and (abs_s[j] > threshold) == is_tone:
            j += 1
        dur = (j - i) / fr
        runs.append((is_tone, dur))
        i = j
    return runs


def runs_to_morse(runs, dot_s):
    morse_tokens = []
    cur = []
    for is_tone, dur in runs:
        if is_tone:
            # classify dot/dash
            if dur < dot_s * 2.0:  # threshold between dot (1x) and dash (3x)
                cur.append('.')
            else:
                cur.append('-')
        else:
            # silence: decide gap type
            if dur < dot_s * 2.0:
                # intra-element gap (1x): continue token
                pass
            elif dur < dot_s * 5.0:
                # between letters gap (3x)
                if cur:
                    morse_tokens.append(''.join(cur))
                    cur = []
            else:
                # between words gap (7x)
                if cur:
                    morse_tokens.append(''.join(cur))
                    cur = []
                morse_tokens.append('/')
    if cur:
        morse_tokens.append(''.join(cur))
    return morse_tokens


def morse_tokens_to_text(tokens):
    out = []
    for t in tokens:
        if t == '/':
            out.append(' ')
        else:
            ch = MORSE_MAP.get(t)
            if ch is None:
                out.append('?')
            else:
                out.append(ch)
    return ''.join(out)


def main():
    parser = argparse.ArgumentParser(description='Decode morse WAV to jumbled text')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Output jumbled text file', default=Path('jumbled_recovered.txt'))
    parser.add_argument('--dot-ms', type=int, help='Dot length ms (override .env)')
    parser.add_argument('--threshold-mult', type=float, default=0.15, help='Energy threshold multiplier of max amplitude')

    args = parser.parse_args()
    env = read_env()
    dot_ms = int(args.dot_ms if args.dot_ms is not None else env.get('MORSE_DOT_MS', '80'))
    dot_s = dot_ms / 1000.0

    inp = args.input
    if not inp.exists():
        print(error(f'Input WAV not found: {inp}'))
        raise SystemExit(1)

    samples, fr = read_wav_samples(inp)
    abs_s = [abs(s) for s in samples]
    maxv = max(abs_s) if abs_s else 0
    threshold = max(100, int(maxv * args.threshold_mult))

    runs = detect_runs(samples, fr, threshold=threshold)
    tokens = runs_to_morse(runs, dot_s)
    text = morse_tokens_to_text(tokens)

    outp = args.output if args.output.is_absolute() else Path.cwd() / args.output
    outp.write_text(text, encoding='utf-8')
    print(success(f'Wrote jumbled text to {color(str(outp), fg="bright_green")}'))


if __name__ == '__main__':
    main()
