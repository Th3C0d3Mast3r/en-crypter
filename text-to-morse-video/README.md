# TEXT-TO-MORSE-VIDEO

This is the type of encryption where I will be taking every word. Now, every word would then be AES Encrypted into a format- and it would yield "the thing". Now, in the thing, I will split "the thing" into blocks of 10 continuous, and then, arrange them in an "ALTERNATING PATTERN" something like:-

1-3-2-5-4 . . . .

This means:-
`1`:- The first 10 continuous characters
`3`:- The next 10 continuous characters after `2`
`2`:- The next 10 continuous characters after `1`
*(and so on)*

Now, this sequence that I have got, that will be converted into **MORSE CODE**. We label this whole thing's morse code as `base_morse`

Once this is done, we would need 2 more `MORSE CODES` that would form a **LOOPING BG MUSIC** - so, it adds noise to the given morse, thus, not allowing one to understand, what even is that thing. That could be something like- a repeating morse of- `sike, thats the wrong number` in plain UTF-8 to Morse conversion and so on. 

Now, we merge them, and upload to YT at a +1.5x Speed *(this is also a variable)*

Thus, the total thing would have the following stuff present for us is:-


> [!NOTE]
> Well, Autocomplete and Copilot came dead handy to understand and write this code faster; as there were things I did not know, and well, `tab` is what helped write faster and build better!
---

## ENCRYPTING PROCESS

The `text-to-morse-video` pipeline first AES-encrypts data and outputs a HEX string to `encrypted.txt`.
After AES, we apply a simple jumbling step controlled by `CHARACTERS_JUMP_LENGTH` in
`text-to-morse-video/.env`.

- Read `encrypted.txt` (hex output from AES).
- Let `jump = CHARACTERS_JUMP_LENGTH` (default 5).
- Partition the hex string into `jump` groups by index modulo `jump`:
	- group[i] contains every character at positions where index % jump == i.
- Write groups in order 0..jump-1 to `jumbled.txt`, one group per line.

This process is reversible: to recover the original hex, read the groups and
interleave characters by taking the first char from group0, then group1, ...,
group(jump-1), then continuing with the second char from each group, and so on.

The provided script `text-to-morse-video/jumbleEncrypted.py` performs the jumbling.

### AES Conversion (`aesConversion.py`)

- Flags:
	- `--input-file`: path to the plaintext `.txt` to encrypt (env default not used)
	- `--output-file`: path to write HEX ciphertext
	- `--key`: override AES_ENCRYPT_KEY from `.env`
	- `--iv`: override AES_INITIAL_VECTOR from `.env`
	- `--mode`: override DEFAULT_AES_MODE from `.env`

- Env variables (in `text-to-morse-video/.env`):
	- `AES_ENCRYPT_KEY` (required)
	- `AES_INITIAL_VECTOR` (required)
	- `DEFAULT_AES_MODE` (e.g. `cbc`)

- Run without overrides (uses `.env`):

	```bash
	python aesConversion.py --input-file input.txt --output-file encrypted.txt
	```

- Run with CLI overrides:

	```bash
	python aesConversion.py --input-file input.txt --output-file encrypted.txt --key MYKEY --iv MYIV --mode cbc
	```

### Data Normalization (`dataToText.py`)

- Flags:
	- `--input-file`: path to input data (csv, json, txt)
	- `--output-file`: path to write normalized text (default `output.txt`)

- Behavior:
	- Reads CSV/JSON/TXT and writes a plain text representation for AES input.

### Jumbling (`jumbleEncrypted.py`)

- Flags:
	- `--input-file`: path to `encrypted.txt` (default `encrypted.txt`)
	- `--output-file`: path to `jumbled.txt` (default `jumbled.txt`)
	- `--jump`: override `CHARACTERS_JUMP_LENGTH` from `.env`

- Env variables:
	- `CHARACTERS_JUMP_LENGTH` (default `5`)

- Run using `.env` value:

	```bash
	python jumbleEncrypted.py
	```

- Run with CLI override:

	```bash
	python jumbleEncrypted.py --input-file encrypted.txt --output-file jumbled.txt --jump 7
	```

### Morse Generation (`toMorseCode.py`)

- Flags:
	- `--input-file`: path to `jumbled.txt` (default `jumbled.txt`)
	- `--output-file`: path to write audio (default `morse.mp3`)
	- `--dot-ms`: dot duration in milliseconds (overrides env)
	- `--freq`: tone frequency in Hz
	- `--volume`: 0.0-1.0 volume
	- `--format`: `mp3` or `wav` (overrides env)

- Env variables (recommended additions to `text-to-morse-video/.env`):
	- `MORSE_DOT_MS=80`
	- `MORSE_TONE_FREQ=750`
	- `MORSE_VOLUME=0.6`
	- `MORSE_OUTPUT_FORMAT=mp3`

- Run with defaults (uses `.env`):

	```bash
	python toMorseCode.py
	```

- Run with CLI overrides:

	```bash
	python toMorseCode.py --input-file jumbled.txt --output-file out.wav --dot-ms 100 --freq 800 --volume 0.5 --format wav
	```

All scripts print colored, verbose messages via the shared `utils` ANSI helpers. For single-file testing, you can override `.env` values via flags as shown above.

## Repository Structure

Top-level files and important folders in this directory:

- `.env` — shared configuration used by all scripts (AES keys, jump length, morse settings, loop word).
- `README.md` — this file.
- `encrypted.txt`, `jumbled.txt`, `morse.wav`, `final.wav` — example outputs produced during runs.
- `encrypt/` — pipeline scripts that perform the full encrypt->morse->mix process (CLI friendly).
- `decrypt/` — (placeholder) intended to hold decryption tools.
- `utils/` — shared helpers used by all scripts:
	- `utils/ansi.py` — ANSI coloring helpers for colored terminal output.
	- `utils/env.py` — locate & read the single shared `.env` file.
	- `utils/aes.py` — AES encrypt/decrypt helper used by the pipeline.

## What This Directory Does

`text-to-morse-video` implements a multi-stage pipeline that:

- Normalizes input data (`dataToText.py`).
- AES-encrypts the normalized text into HEX (`aesConversion.py`).
- Jumbles the ciphertext into groups based on `CHARACTERS_JUMP_LENGTH` (`jumbleEncrypted.py`).
- Converts the jumbled HEX into Morse and synthesizes audio (`toMorseCode.py`).
- Generates a looping background Morse from `RANDOM_WORD_ON_LOOP` and mixes it with the main Morse (`mergeMorseLoop.py`).
- A single-run pipeline `encrypt/encrypt.py` ties these steps together and can process a file or a directory (modes: single combined output or per-file outputs).

All scripts default to settings in the shared `.env` but expose CLI flags to override values for testing.

## Recent Changes (what was added)

- Added `utils/ansi.py` and wired colored output across scripts.
- Added `utils/env.py` so every script reads the single shared `text-to-morse-video/.env`.
- Implemented `jumbleEncrypted.py`, `toMorseCode.py`, `mergeMorseLoop.py` for the morse pipeline.
- Added `encrypt/encrypt.py` pipeline runner with directory mode, ETA, and CLI overrides.
- Updated README with per-script flags and usage examples.

If any of the above descriptions don't match how you want the pipeline to behave, tell me which part to adjust and I will update the docs and code accordingly.

### Decrypting / Recovery (decrypt/)

The `decrypt` folder contains tools to reverse the pipeline. Important scripts:

- `decrypt/remove_loop.py` — subtracts the `RANDOM_WORD_ON_LOOP` morse loop from a mixed WAV to recover the main morse.
- `decrypt/wav_to_jumbled.py` — decodes a cleaned mono WAV into jumbled UTF characters (produces `jumbled_recovered.txt`).
- `decrypt/rev_jumble.py` — reverses the jumbling step to rebuild the AES HEX ciphertext.
- `utils/rev_aes.py` — central AES decryption utility (moved to `utils/`) — decrypts HEX ciphertext to plaintext using `AES_ENCRYPT_KEY` and `AES_INITIAL_VECTOR` from the shared `.env` or CLI overrides.

Typical recovery workflow:

1. Convert final MP3 to mono WAV if needed:

```bash
ffmpeg -i final.mp3 -ac 1 -ar 44100 final.wav
```

2. Remove the loop overlay:

```bash
python decrypt/remove_loop.py --input final.wav --output clean.wav
```

3. Decode the cleaned WAV to jumbled text:

```bash
python decrypt/wav_to_jumbled.py --input clean.wav --output jumbled_recovered.txt
```

4. Recover AES HEX and plaintext:

```bash
python decrypt/rev_jumble.py --input jumbled_recovered.txt --output encrypted_recovered.txt
python -m utils.rev_aes --input encrypted_recovered.txt --output recovered.txt
```

All decrypt scripts read defaults from the shared `text-to-morse-video/.env`. Use CLI flags to override settings for tuning (e.g. `--dot-ms`, `--freq`, `--loop-volume`).

