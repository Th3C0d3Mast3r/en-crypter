# TODO

## Goal
Build `text-to-image` as a reversible encrypted byte-to-image pipeline, preferably in C, with exact file/folder reconstruction.

## Phase 1: Format Design
- Define the overall pipeline: `files/folder -> manifest -> compress(optional) -> encrypt -> bytes -> pixels -> image`.
- Define mode semantics:
  - `mode 0`: combine one file/folder into one logical archive, possibly spanning multiple images.
  - `mode 1`: process each file independently into its own image or image set.
- Define supported inputs for v1:
  - `.txt`
  - `.json`
  - `.csv`
- Decide the first lossless image format:
  - start with `PPM` or `BMP`
  - add `PNG` later

## Phase 2: Payload Manifest
- Design a manifest format for exact reconstruction.
- Store, per file:
  - relative path
  - size
  - SHA-256
  - raw bytes or Base64 bytes
- Add payload metadata:
  - format version
  - mode
  - file count
- Make sure nested folders can be restored exactly.

## Phase 3: Binary Header
- Design a binary header stored inside the image payload.
- Include:
  - magic bytes
  - version
  - flags
  - chunk index
  - total chunks
  - payload length
  - checksum or hash
- Reject invalid or truncated data cleanly.

## Phase 4: Raw Byte Codec
- Implement byte-to-pixel mapping.
- Baseline mapping:
  - 3 bytes -> 1 RGB pixel
- Store the real payload length so padded bytes can be removed during decode.
- Implement the reverse pixel-to-byte mapping.
- Verify that random bytes round-trip exactly.

## Phase 5: Image Reader/Writer
- Implement a minimal writer for `PPM` or `BMP`.
- Implement the matching reader.
- Keep this part independent from encryption first.
- Verify:
  - bytes -> image -> bytes
  - output matches exactly

## Phase 6: Compression
- Optionally compress the manifest bytes before encryption.
- Prefer a standard library approach such as zlib if used.
- Keep compression optional in v1 if it slows development.

## Phase 7: Encryption
- Implement encryption after the manifest layer is stable.
- Recommended order:
  - best: authenticated encryption
  - acceptable: AES-CBC plus integrity check
- Required pieces:
  - key handling
  - IV or nonce handling
  - encrypt/decrypt functions
  - tamper detection
- Verify decrypt(encrypt(data)) == data.

## Phase 8: Chunking Across Images
- Split encrypted payload by image capacity, not by source text length.
- Store chunk number and total chunk count in the header.
- Implement reassembly before decryption.
- Fail clearly if a chunk is missing.

## Phase 9: File/Folder Restore
- Decode all chunks.
- Reassemble encrypted bytes.
- Decrypt.
- Parse manifest.
- Restore original files and folder structure.
- Verify hashes before writing restored content.

## Phase 10: CLI Design
- Plan one binary with subcommands:
  - `tti encrypt`
  - `tti decrypt`
  - `tti inspect`
  - `tti verify`
- Example flags:
  - `--input`
  - `--output-dir`
  - `--mode`
  - `--format`
  - `--key`
  - `--iv` or `--nonce`

## Phase 11: Validation
- Add a byte codec round-trip test.
- Add a header validation test.
- Add a single-file round-trip test.
- Add a nested-folder round-trip test.
- Add a multi-image chunking test.
- Add wrong-key and corrupted-image failure tests.

## Phase 12: Nice-To-Haves
- Add PNG support.
- Add better metadata inspection.
- Add a debug mode that dumps:
  - manifest
  - encrypted bytes
  - chunk layout
- Add interoperability tests if part of the pipeline remains in Python.

## Suggested Build Order
1. PPM/BMP reader-writer
2. Byte-to-pixel codec
3. Header format
4. Single-file round-trip without encryption
5. Manifest format
6. Folder restore
7. Encryption layer
8. Multi-image chunking
9. CLI
10. PNG support

## Rules To Keep
- Use only lossless image formats.
- Do not chunk by plaintext character count.
- Do not rely on visual patterns for security.
- Keep every stage reversible.
- Keep format versioned from day one.
