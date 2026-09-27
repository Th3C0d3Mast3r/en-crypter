"""Mix main morse (from jumbled) with a looping morse background word.

Reads `jumbled.txt`, converts to morse (uses same `toMorseCode` logic), reads
`RANDOM_WORD_ON_LOOP` from `.env`, converts that to morse and repeats it to
match the length of the main morse audio, then mixes samples and writes `final.mp3` or `final.wav`.
"""
from pathlib import Path
import argparse
import struct
import wave
import math
import sys
from typing import List

# ensure local modules and project root import correctly
base = Path(__file__).resolve().parent
project_root = base.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(base) not in sys.path:
    sys.path.insert(0, str(base))

from utils.ansi import success, error, info, color
from toMorseCode import text_to_morse, synthesize_morse, write_wav, try_convert_to_mp3
from utils.env import read_env

env = read_env(base.parent / ".env")


def mix_pcm(pcm_a: bytes, pcm_b: bytes, volume_a: float = 1.0, volume_b: float = 0.5) -> bytes:
    # unpack 16-bit signed samples
    fmt = "<{}h".format(len(pcm_a) // 2)
    samples_a = list(struct.unpack(fmt, pcm_a))
    samples_b = list(struct.unpack(fmt, pcm_b))

    out = []
    for i in range(len(samples_a)):
        a = int(samples_a[i] * volume_a)
        b = int(samples_b[i] * volume_b) if i < len(samples_b) else 0
        mixed = a + b
        # clamp
        if mixed > 32767:
            mixed = 32767
        if mixed < -32768:
            mixed = -32768
        out.append(mixed)

    return struct.pack(fmt, *out)


def main():
    parser = argparse.ArgumentParser(description="Mix main morse with looping background morse")
    parser.add_argument("--jumbled", type=Path, help="Jumbled input file (default: jumbled.txt in dir)")
    parser.add_argument("--output", type=Path, help="Final mixed output (default based on env MORSE_OUTPUT_FORMAT)")
    parser.add_argument("--loop-word", type=str, help="Override RANDOM_WORD_ON_LOOP from .env")
    parser.add_argument("--dot-ms", type=int, help="Dot duration ms (override .env)")
    parser.add_argument("--freq", type=int, help="Tone frequency Hz (override .env)")
    parser.add_argument("--loop-volume", type=float, default=None, help="Volume for looping background (0-1)")
    parser.add_argument("--main-volume", type=float, default=None, help="Volume for main morse (0-1)")
    parser.add_argument("--format", choices=["mp3", "wav"], help="Output format override")

    args = parser.parse_args()

    env = read_env(base.parent / ".env")

    # Resolve defaults from env and naming conventions
    jumbled_arg = args.jumbled if args.jumbled is not None else Path("jumbled.txt")
    jumbled_path = jumbled_arg if jumbled_arg.is_absolute() else base / jumbled_arg

    out_format = args.format.lower() if args.format else env.get("MORSE_OUTPUT_FORMAT", "mp3").lower()
    default_out_name = "final." + ("mp3" if out_format == "mp3" else "wav")
    out_arg = args.output if args.output is not None else Path(default_out_name)
    out_path = out_arg if out_arg.is_absolute() else base / out_arg

    dot_ms = int(env.get("MORSE_DOT_MS", "80")) if args.dot_ms is None else args.dot_ms
    freq = int(env.get("MORSE_TONE_FREQ", "750")) if args.freq is None else args.freq
    loop_word = args.loop_word if args.loop_word is not None else env.get("RANDOM_WORD_ON_LOOP", "")
    loop_volume = args.loop_volume if args.loop_volume is not None else float(env.get("MORSE_LOOP_VOLUME", "0.5"))
    main_volume = args.main_volume if args.main_volume is not None else float(env.get("MORSE_MAIN_VOLUME", "1.0"))

    if not jumbled_path.exists():
        print(error(f"Jumbled file not found: {jumbled_path}"))
        raise SystemExit(1)

    jumbled = jumbled_path.read_text(encoding="utf-8").strip()
    joined = "".join(jumbled.splitlines())
    main_morse = text_to_morse(joined)

    if not loop_word:
        print(info("No RANDOM_WORD_ON_LOOP provided; output will contain only main morse"))
        pcm_main = synthesize_morse(main_morse, dot_ms=dot_ms, freq=freq, volume=main_volume)
        # choose format
        if out_format == "mp3":
            tmp = out_path.with_suffix('.wav')
            write_wav(tmp, pcm_main)
            ok = try_convert_to_mp3(tmp, out_path)
            if ok:
                tmp.unlink(missing_ok=True)
                print(success(f"Wrote final MP3 to {color(str(out_path), fg='bright_green')}"))
            else:
                print(info("Could not convert to MP3; wrote WAV instead."))
                write_wav(out_path.with_suffix('.wav'), pcm_main)
                print(success(f"Wrote final WAV to {color(str(out_path.with_suffix('.wav')), fg='bright_green')}"))
        else:
            write_wav(out_path, pcm_main)
            print(success(f"Wrote final WAV to {color(str(out_path), fg='bright_green')}"))
        return

    loop_morse = text_to_morse(loop_word)

    pcm_main = synthesize_morse(main_morse, dot_ms=dot_ms, freq=freq, volume=main_volume)
    pcm_loop_single = synthesize_morse(loop_morse, dot_ms=dot_ms, freq=freq, volume=1.0)

    # repeat loop to at least match length of main
    repeats = math.ceil(len(pcm_main) / len(pcm_loop_single)) if len(pcm_loop_single) > 0 else 1
    pcm_loop = pcm_loop_single * repeats
    pcm_loop = pcm_loop[: len(pcm_main)]

    mixed = mix_pcm(pcm_main, pcm_loop, volume_a=main_volume, volume_b=loop_volume)

    if out_format == "mp3":
        tmp = out_path.with_suffix('.wav')
        write_wav(tmp, mixed)
        ok = try_convert_to_mp3(tmp, out_path)
        if ok:
            tmp.unlink(missing_ok=True)
            print(success(f"Wrote final MP3 to {color(str(out_path), fg='bright_green')}"))
        else:
            print(info("Could not convert to MP3; wrote WAV instead."))
            write_wav(out_path.with_suffix('.wav'), mixed)
            print(success(f"Wrote final WAV to {color(str(out_path.with_suffix('.wav')), fg='bright_green')}"))
    else:
        write_wav(out_path, mixed)
        print(success(f"Wrote final WAV to {color(str(out_path), fg='bright_green')}"))


if __name__ == "__main__":
    main()
