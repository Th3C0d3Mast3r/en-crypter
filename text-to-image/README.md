# Text-To-Image

This directory builds a Python-first reversible encrypted byte-to-image pipeline.

The design target matches the spirit of `text-to-morse-video`, but the final carrier is a lossless image instead of Morse audio.

The main rule is: do not chunk by character count. Work on raw bytes, then split by image capacity.

## Intended Pipeline

The planned encryption flow is:

1. Read one file or a folder of supported files.
2. Build a manifest payload containing relative paths, sizes, hashes, and file bytes.
3. AES-encrypt that payload using values loaded from `.env`.
4. Jumble the encrypted output so the ciphertext is rearranged before image encoding.
5. Attach a binary header for chunk metadata.
6. Convert the resulting bytes into RGB pixel bytes.
7. Write those RGB bytes to a lossless image such as binary PPM.

The planned decrypt flow is:

1. Read one image or a set of images.
2. Recover the raw RGB bytes.
3. Parse the binary header and reassemble chunks.
4. Reverse the jumbling.
5. AES-decrypt using the same `.env` values.
6. Parse the manifest.
7. Restore the original file or folder exactly.

That means a raw image by itself is not enough. The decoder still needs the correct environment values such as the AES key, IV or nonce, and jumble settings.

## Directory Layout

- `encrypt/`
   Encryption-side runners and jumbling helpers.
- `decrypt/`
   Decryption-side runners and reverse-jumbling helpers.
- `image_ppm.py`
   Lossless binary PPM reader and writer.
- `byte_codec.py`
   Byte-to-RGB packing and unpacking.
- `header.py`
   Binary chunk header packing and parsing.
- `manifest.py`
   File manifest build and restore logic.
- `chunk.py`
   Capacity calculations for future multi-image chunking.
- `cli.py`
   Small wrapper that dispatches to `encrypt/` or `decrypt/`.

## How To Read The Code

Read the files in this order and read them with one question in mind: what single responsibility does this file own?

1. `image_ppm.py`
   This is the image container layer. Learn how raw RGB bytes are stored and recovered from a binary PPM file.
2. `byte_codec.py`
   This is the byte-to-pixel layer. Learn how arbitrary bytes are padded into exact RGB triplets and reversed.
3. `header.py`
   This is the chunk metadata layer. Learn how version, flags, payload length, and chunk counts are packed into bytes.
4. `manifest.py`
   This is the archive layer. Learn how a file or folder becomes one deterministic payload.
5. `encrypt/jumble.py`
   This is the obfuscation layer. Learn how encrypted HEX is rearranged before image encoding.
6. `decrypt/rev_jumble.py`
   This is the reversal of the jumble layer. Learn how the original encrypted HEX is reconstructed.
7. `encrypt/encrypt.py`
   This is the encryption pipeline runner. Learn how `.env`, AES, jumbling, manifest building, and image writing are wired together.
8. `decrypt/decrypt.py`
   This is the decode pipeline runner. Learn how an image is turned back into the original files.
9. `chunk.py`
   This is the image-capacity layer. Learn how payloads are split to fit one or more images.
10. `cli.py`
   This is the top-level wrapper. Learn how commands are dispatched.

### How To Read Each File Properly

For each file, read in this order:

1. Start with the function names and signatures.
2. Identify the input type and output type of each function.
3. Write down what assumptions the file makes.
4. Ignore future pipeline details and focus only on what that file promises to do.
5. Run or test that one file in isolation before moving forward.

Example:

- `image_ppm.py`: ask "what is a valid in-memory image and how is it written to disk?"
- `byte_codec.py`: ask "if I give this file 5 bytes, how many RGB bytes come out and how do I reverse them?"
- `manifest.py`: ask "if I give this file 3 files, what exact payload bytes are produced?"

## Runtime Shape

This pipeline should mirror the existing repo conventions:

- Load defaults from `.env` using `utils.env.read_env`.
- Use `utils.ansi` for colored terminal output.
- Reuse the shared AES style from the repo through `utils.aes.AESUtils`.
- Add a jumbling stage before image encoding.
- Produce images that look like random dots because they encode encrypted and jumbled bytes.

## Commands

These commands now work for the current single-image pipeline.

### Single File

```bash
cd text-to-image
python encrypt/encrypt.py --input ./data/file.txt --mode 1 --output-dir ./tti_out
```

Expected behavior:

- Build a manifest for the single file.
- AES-encrypt using `.env` values.
- Jumble the encrypted data.
- Convert the result to one PPM image.
- Write outputs under `encrypt/tti_out/file/`.

### Folder To One Combined Output

```bash
cd text-to-image
python encrypt/encrypt.py --input ./data_folder --mode 0 --output-dir ./tti_out
```

Expected behavior:

- Read all supported files from the folder.
- Build one combined manifest.
- Encrypt and jumble the combined payload.
- Convert the combined payload into one PPM image.
- Write the image and helper text files under `encrypt/tti_out/`.

### Folder To One Output Per File

```bash
cd text-to-image
python encrypt/encrypt.py --input ./data_folder --mode 1 --output-dir ./tti_out
```

Expected behavior:

- Process each file independently.
- Generate one output directory per file.
- Allow each file to be decrypted independently later.

### Decrypt

```bash
cd text-to-image
python decrypt/decrypt.py --input ./encrypt/tti_out/file/final.ppm --output-dir ./restored
```

Expected behavior:

- Read one image.
- Reverse jumbling.
- AES-decrypt with the same `.env` values.
- Restore the original file or folder.

## Configuration Direction

This pipeline should use environment-backed settings similar to `text-to-morse-video`.

Expected values include:

- `AES_ENCRYPT_KEY`
- `AES_INITIAL_VECTOR`
- `DEFAULT_AES_MODE`
- `CHARACTERS_JUMP_LENGTH`
- `TTI_IMAGE_WIDTH`
- output image format settings

## Notes

- Start with PPM because it is lossless and easy to inspect.
- Keep every stage reversible before adding the next stage.
- Chunk by image byte capacity, not by plaintext size.
- The current implementation writes one image per payload; multi-image chunking is still the next expansion step.

> [!NOTE]
> To see the image, use the `pnmtopng` CLI on Ubuntu. To use that, first run the `sudo apt insall netpbm` and then, the above command as `pnmtopng <inputFile> > <outputFile>`