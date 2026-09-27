# TEXT-TO-MORSE-AUDIO

`text-to-morse-video` is a reversible file-to-audio encryption pipeline.

It takes one file or a folder of files, wraps them into a deterministic payload,
AES-encrypts that payload, rearranges the ciphertext, converts it into Morse audio,
and then hides that Morse under a looping background Morse track.

The decrypt side reverses the same steps and restores the original file contents.

## What It Does

The pipeline is designed for these cases:

- Encrypt a single text, JSON, or CSV file into Morse audio.
- Encrypt a whole folder of supported files into one output audio file.
- Encrypt a folder so each file gets its own separate audio output.
- Recover the original files from the produced WAV audio.
- Use structured data exports such as database dumps converted to CSV or JSON.

Supported input file types:

- `.txt`
- `.json`
- `.csv`

## How The Pipeline Works

The working flow is:

1. Read one file or many files.
2. Build a manifest payload containing relative file paths, file sizes, hashes, and raw file bytes encoded in Base64.
3. AES-encrypt that payload into HEX.
4. Jumble the HEX by splitting it into `CHARACTERS_JUMP_LENGTH` groups.
5. Convert the jumbled HEX to Morse.
6. Synthesize Morse as audio.
7. Generate a second Morse signal from `RANDOM_WORD_ON_LOOP`.
8. Overlay both audio streams into the final output.

The reverse flow is:

1. Read the final WAV.
2. Remove the looping Morse overlay.
3. Decode the main Morse back into jumbled HEX text.
4. Reverse the jumbling.
5. AES-decrypt the recovered HEX.
6. Rebuild the original file or folder from the manifest payload.

## Project Structure

- `.env`: runtime configuration for AES, jumbling, Morse timing, and loop word.
- `.env.sample`: sample configuration.
- `encrypt/`: encryption-side modules.
- `decrypt/`: decryption-side modules.
- `payload.py`: manifest builder/restorer used for deterministic file reconstruction.

Main modules:

- `encrypt/encrypt.py`: full encryption pipeline runner.
- `decrypt/decrypt.py`: full decryption pipeline runner.
- `encrypt/aesConversion.py`: AES encryption helper CLI.
- `encrypt/jumbleEncrypted.py`: HEX jumbling helper CLI.
- `encrypt/toMorseCode.py`: jumbled text to Morse audio.
- `encrypt/mergeMorseLoop.py`: mixes main Morse and loop Morse.
- `decrypt/remove_loop.py`: subtracts loop Morse from the final WAV.
- `decrypt/wav_to_jumbled.py`: decodes Morse WAV back to jumbled text.
- `decrypt/rev_jumble.py`: reconstructs original encrypted HEX.
- `../utils/rev_aes.py`: decrypts recovered HEX to plaintext.

## Configuration

Create `.env` using `.env.sample`.

> [!NOTE]
> - AES key length must be `16`, `24`, or `32` bytes.
> - AES IV must be exactly `16` bytes.
> - Only `cbc` mode is supported right now.
> - `MORSE_OUTPUT_FORMAT=mp3` needs `ffmpeg` available through `pydub`.
> - For decryption and testing, `wav` output is easier and more stable.

## Installation

From the repository root:

```bash
pip install -r requirements.txt
```

Optional but recommended for MP3 support:

```bash
sudo apt install ffmpeg
```

## Full Encryption Usage

Run from the repository root:

```bash
python text-to-morse-video/encrypt/encrypt.py --input <path> --mode <0|1>
```

Arguments:

- `--input`: file or folder to encrypt.
- `--mode 0`: combine the input set into one final output.
- `--mode 1`: generate one output per input file.
- `--output-dir`: output directory. Default is `encrypted_output` inside `encrypt/`.
- `--key`: override `AES_ENCRYPT_KEY`.
- `--iv`: override `AES_INITIAL_VECTOR`.
- `--jump`: override `CHARACTERS_JUMP_LENGTH`.
- `--dot-ms`: override `MORSE_DOT_MS`.
- `--freq`: override `MORSE_TONE_FREQ`.
- `--loop-word`: override `RANDOM_WORD_ON_LOOP`.
- `--loop-volume`: override loop volume.
- `--main-volume`: override main Morse volume.
- `--format`: `wav` or `mp3`.

### Mode 0: Folder To Single Output

This is the right mode when you want one audio output containing a whole dataset.

Example:

```bash
python text-to-morse-video/encrypt/encrypt.py \
	--input ./exports \
	--mode 0 \
	--output-dir ./tmv_out \
	--format wav
```

If `./exports` contains:

- `users.json`
- `orders.csv`
- `notes.txt`

then one combined encrypted payload is produced and written as:

- `./tmv_out/encrypted.txt`
- `./tmv_out/jumbled.txt`
- `./tmv_out/final.wav` or `final.mp3`

Use this mode when:

- you want one portable encrypted audio artifact,
- you want to archive one full export,
- you are shipping one combined dataset.

### Mode 1: One Output Per File

This mode processes each file independently.

Example:

```bash
python text-to-morse-video/encrypt/encrypt.py \
	--input ./exports \
	--mode 1 \
	--output-dir ./tmv_out \
	--format wav
```

Output layout will look like:

```text
tmv_out/
	users/
		encrypted.txt
		jumbled.txt
		final.wav
	orders/
		encrypted.txt
		jumbled.txt
		final.wav
	notes/
		encrypted.txt
		jumbled.txt
		final.wav
```

Use this mode when:

- each file should be decrypted independently,
- you want smaller audio artifacts,
- you are processing datasets file by file.

## Full Decryption Usage

Run from the repository root:

```bash
python text-to-morse-video/decrypt/decrypt.py --input <wav-or-folder> --mode <0|1>
```

Arguments:

- `--input`: a final WAV file or a folder of WAV files.
- `--mode 0`: combined recovery into one output directory.
- `--mode 1`: restore one result per input file.
- `--output-dir`: target directory for restored files.
- `--jump`: override `CHARACTERS_JUMP_LENGTH`.
- `--dot-ms`: override `MORSE_DOT_MS`.
- `--freq`: override `MORSE_TONE_FREQ`.
- `--loop-word`: override `RANDOM_WORD_ON_LOOP`.
- `--loop-volume`: override loop volume.
- `--key`: override `AES_ENCRYPT_KEY`.
- `--iv`: override `AES_INITIAL_VECTOR`.

### Decrypt One Combined Audio

```bash
python text-to-morse-video/decrypt/decrypt.py \
	--input ./tmv_out/final.wav \
	--mode 0 \
	--output-dir ./restored
```

If the source audio came from folder mode `0`, the original folder contents are restored under `./restored`.

### Decrypt Per-File Audio

```bash
python text-to-morse-video/decrypt/decrypt.py \
	--input ./tmv_out/users/final.wav \
	--mode 1 \
	--output-dir ./restored
```

That restores the original file under a subdirectory inside `./restored`.

## Using Each Module Directly

You do not have to run the full pipeline every time. Each stage can be used directly.

### 1. Normalize Data

```bash
python text-to-morse-video/encrypt/dataToText.py \
	--input-file ./data/orders.csv \
	--output-file ./output.txt
```

Use this when you only want a plain text rendering of CSV, JSON, or TXT data.

### 2. AES Encrypt Plaintext

```bash
python text-to-morse-video/encrypt/aesConversion.py \
	--input-file ./output.txt \
	--output-file ./encrypted.txt
```

This writes ciphertext HEX.

### 3. Jumble The HEX

```bash
python text-to-morse-video/encrypt/jumbleEncrypted.py \
	--input-file ./encrypted.txt \
	--output-file ./jumbled.txt
```

This writes one jumble group per line.

### 4. Convert Jumbled Text To Morse Audio

```bash
python text-to-morse-video/encrypt/toMorseCode.py \
	--input-file ./jumbled.txt \
	--output-file ./morse.wav \
	--format wav
```

### 5. Mix Loop Morse With Main Morse

```bash
python text-to-morse-video/encrypt/mergeMorseLoop.py \
	--jumbled ./jumbled.txt \
	--output ./final.wav \
	--format wav
```

### 6. Remove Loop During Recovery

```bash
python text-to-morse-video/decrypt/remove_loop.py \
	--input ./final.wav \
	--output ./clean.wav
```

### 7. Decode Clean WAV Back To Jumbled Text

```bash
python text-to-morse-video/decrypt/wav_to_jumbled.py \
	--input ./clean.wav \
	--output ./jumbled_recovered.txt
```

### 8. Reverse The Jumble

```bash
python text-to-morse-video/decrypt/rev_jumble.py \
	--input ./jumbled_recovered.txt \
	--output ./encrypted_recovered.txt
```

### 9. AES Decrypt Recovered HEX

```bash
python -m utils.rev_aes \
	--input ./encrypted_recovered.txt \
	--output ./recovered.txt
```

## Using It With Real Database Data

This project does not connect directly to MySQL, PostgreSQL, MongoDB, or SQLite.
The correct approach is to export your database data into supported files and then encrypt those files.

Recommended patterns:

### Option 1: Export Tables To CSV

Good for:

- relational tables,
- analytics exports,
- tabular snapshots.

Example layout:

```text
db_export/
	users.csv
	orders.csv
	invoices.csv
```

Encrypt all tables into one audio:

```bash
python text-to-morse-video/encrypt/encrypt.py \
	--input ./db_export \
	--mode 0 \
	--output-dir ./db_audio \
	--format wav
```

### Option 2: Export Documents To JSON

Good for:

- MongoDB collections,
- API payload archives,
- nested records.

Example layout:

```text
db_export/
	users.json
	sessions.json
	audit_log.json
```

Then run the same folder encryption flow.

### Option 3: Application Snapshot Folder

Good for mixed exports from a real system.

Example:

```text
snapshot/
	customers.csv
	config.json
	notes.txt
	reports/
		daily.json
		summary.txt
```

The current pipeline recursively discovers supported files inside folders, so nested supported files are included automatically.

### Option 4: One File Per Dataset

If you want each table or collection to decrypt separately, use mode `1`.

```bash
python text-to-morse-video/encrypt/encrypt.py \
	--input ./db_export \
	--mode 1 \
	--output-dir ./db_audio \
	--format wav
```

That produces one audio artifact per input file.

## Recommended Real-World Workflows

### Workflow A: Archive An Entire Export

1. Export your database into a folder of CSV or JSON files.
2. Run encrypt mode `0` on that folder.
3. Store the resulting `final.wav` or `final.mp3`.
4. Decrypt with `decrypt.py` when restoration is needed.

### Workflow B: Encrypt Table By Table

1. Export each table or collection as a separate file.
2. Run encrypt mode `1`.
3. Keep the resulting per-file output directories.
4. Decrypt only the files you need later.

### Workflow C: Manual Stage Debugging

1. Run `aesConversion.py`.
2. Run `jumbleEncrypted.py`.
3. Run `toMorseCode.py`.
4. Run `mergeMorseLoop.py`.
5. Reverse with `remove_loop.py`, `wav_to_jumbled.py`, and `rev_jumble.py`.

This is the right workflow if you are tuning Morse timing or checking where corruption happens.

## Important Practical Notes

- Prefer `wav` while testing. It avoids MP3 compression artifacts.
- Use the same `.env` values for encryption and decryption.
- `RANDOM_WORD_ON_LOOP` must stay identical across both sides.
- `CHARACTERS_JUMP_LENGTH` must match on both sides.
- AES key and IV must match on both sides.
- If you change Morse timing, decrypt with the same timing.
- Folder input only processes supported file types.

## Output Examples

Combined mode output:

```text
encrypted_output/
	encrypted.txt
	jumbled.txt
	final.wav
```

Per-file mode output:

```text
encrypted_output/
	file_a/
		encrypted.txt
		jumbled.txt
		final.wav
	file_b/
		encrypted.txt
		jumbled.txt
		final.wav
```

Decrypted output for a combined manifest:

```text
decrypted_output/
	users.csv
	orders.csv
	reports/
		weekly.json
```

## Troubleshooting

`ModuleNotFoundError`:

- install dependencies with `pip install -r requirements.txt`

`Could not convert to MP3`:

- install `ffmpeg`, or use `--format wav`

`Invalid padding bytes` or HEX decode errors:

- make sure key, IV, jump length, Morse timing, and loop word all match between encryption and decryption
- prefer WAV for validation before trying MP3

No files found in folder mode:

- check that the folder contains supported `.txt`, `.json`, or `.csv` files

## Minimal Working Examples

Encrypt one file:

```bash
python text-to-morse-video/encrypt/encrypt.py \
	--input ./message.txt \
	--mode 1 \
	--output-dir ./out \
	--format wav
```

Decrypt it back:

```bash
python text-to-morse-video/decrypt/decrypt.py \
	--input ./out/message/final.wav \
	--mode 1 \
	--output-dir ./restored
```

Encrypt one folder into one audio:

```bash
python text-to-morse-video/encrypt/encrypt.py \
	--input ./dataset \
	--mode 0 \
	--output-dir ./out \
	--format wav
```

Decrypt it back:

```bash
python text-to-morse-video/decrypt/decrypt.py \
	--input ./out/final.wav \
	--mode 0 \
	--output-dir ./restored
```

