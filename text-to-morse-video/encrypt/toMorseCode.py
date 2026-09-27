"""Convert `jumbled.txt` into Morse audio (WAV or MP3).

Reads jumbled input, encodes characters to Morse, synthesizes audio, and writes
an output file. Uses `text-to-morse-video/.env` values unless overridden via CLI.

CLI flags: `--input-file`, `--output-file`, `--dot-ms`, `--freq`, `--volume`, `--format`.
"""
from pathlib import Path
import math
import wave
import struct
import argparse
import sys
from typing import Dict

# ensure local modules and project root import correctly
base = Path(__file__).resolve().parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(base) not in sys.path:
    sys.path.insert(0, str(base))

from utils.ansi import success, error, info, color
from utils.env import read_env

env = read_env(base.parent / ".env")


# Basic international Morse mapping for letters and digits
MORSE: Dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    # common punctuation that may appear
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-", "&": ".-...",
    ":": "---...", ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-",
    "_": "..--.-", '"': ".-..-.", "$": "...-..-", "@": ".--.-.",
}


def text_to_morse(text: str) -> str:
    parts = []
    for ch in text:
        if ch.isspace():
            parts.append("/")
            continue
        code = MORSE.get(ch.upper())
        if code:
            parts.append(code)
        else:
            # for unknown characters, include space
            parts.append(" ")
    return " ".join(parts)


def synthesize_morse(morse: str, dot_ms: int, freq: int, volume: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Synthesize PCM16 mono bytes for the given morse string.

    - `.` is dot, `-` is dash, space separates letters, `/` denotes word gap.
    """
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
            v = int(amplitude * math.sin(2 * math.pi * freq * t))
            samples.append(v)

    def silence(duration_s: float):
        n = int(sample_rate * duration_s)
        for _ in range(n):
            samples.append(0)

    tokens = morse.split(" ")
    first_token = True
    for token in tokens:
        if not first_token:
            # between letters
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
                # unknown symbol -> short silence
                silence(intra_element_s)
            # intra-element gap (silence) after each dot/dash except last
            if i != len(token) - 1:
                silence(intra_element_s)

    # trailing silence buffer to ensure final tone completion
    silence(between_words_s)

    # pack into bytes
    data = struct.pack("<{}h".format(len(samples)), *samples)
    return data


def write_wav(path: Path, pcm_bytes: bytes, sample_rate: int = 44100):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def try_convert_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
    """Try to convert WAV to MP3 using pydub (ffmpeg). Returns True on success."""
    try:
        from pydub import AudioSegment
    except Exception:
        return False
    try:
        seg = AudioSegment.from_wav(str(wav_path))
        seg.export(str(mp3_path), format="mp3")
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert jumbled text to Morse audio")
    parser.add_argument("--input-file", type=Path, default=Path("jumbled.txt"), help="Jumbled input file")
    parser.add_argument("--output-file", type=Path, default=Path("morse.mp3"), help="Output audio file (mp3 or wav)")
    parser.add_argument("--dot-ms", type=int, help="Dot duration in milliseconds (override .env)")
    parser.add_argument("--freq", type=int, help="Tone frequency in Hz")
    parser.add_argument("--volume", type=float, help="Volume 0.0-1.0")
    parser.add_argument("--format", choices=["mp3", "wav"], help="Output format override")

    args = parser.parse_args()

    env = read_env(base.parent / ".env")
    dot_ms = int(env.get("MORSE_DOT_MS", "80")) if args.dot_ms is None else args.dot_ms
    freq = int(env.get("MORSE_TONE_FREQ", "750")) if args.freq is None else args.freq
    volume = float(env.get("MORSE_VOLUME", "0.6")) if args.volume is None else args.volume
    out_format = (env.get("MORSE_OUTPUT_FORMAT", "mp3") if args.format is None else args.format).lower()

    inp = args.input_file if args.input_file.is_absolute() else base / args.input_file
    if not inp.exists():
        print(error(f"Input file not found: {inp}"))
        raise SystemExit(1)

    jumbled = inp.read_text(encoding="utf-8").strip()
    # join lines (groups) with no separator to reconstruct jumbled hex stream
    joined = "".join(jumbled.splitlines())

    morse = text_to_morse(joined)

    pcm = synthesize_morse(morse, dot_ms=dot_ms, freq=freq, volume=volume)

    out_path = args.output_file if args.output_file.is_absolute() else base / args.output_file
    # if user requested mp3 but conversion tools unavailable, write wav and notify
    if out_format == "mp3":
        # write temporary wav
        tmp_wav = out_path.with_suffix(".wav")
        write_wav(tmp_wav, pcm)
        ok = try_convert_to_mp3(tmp_wav, out_path)
        if ok:
            tmp_wav.unlink(missing_ok=True)
            print(success(f"Wrote Morse MP3 to {color(str(out_path), fg='bright_green')}"))
        else:
            print(info("Could not convert to MP3 (ffmpeg/pydub missing). Wrote WAV instead."))
            write_wav(out_path.with_suffix(".wav"), pcm)
            print(success(f"Wrote Morse WAV to {color(str(out_path.with_suffix('.wav')), fg='bright_green')}"))
    else:
        write_wav(out_path, pcm)
        print(success(f"Wrote Morse WAV to {color(str(out_path), fg='bright_green')}"))


if __name__ == "__main__":
    main()
