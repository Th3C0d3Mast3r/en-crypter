from pathlib import Path
import argparse
from .ansi import success, error, color
from .env import read_env
from .aes import AESUtils


def main():
    parser = argparse.ArgumentParser(description="Decrypt HEX ciphertext with AES and output plaintext")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--key", type=str, help="Override AES_ENCRYPT_KEY from .env")
    parser.add_argument("--iv", type=str, help="Override AES_INITIAL_VECTOR from .env")

    args = parser.parse_args()
    env = read_env()
    key = args.key or env.get("AES_ENCRYPT_KEY")
    iv = args.iv or env.get("AES_INITIAL_VECTOR")

    if not key or not iv:
        print(error("AES key/iv not provided via args or .env"))
        raise SystemExit(1)

    inp = args.input
    if not inp.exists():
        print(error(f"Input not found: {inp}"))
        raise SystemExit(1)

    ciphertext_hex = inp.read_text(encoding="utf-8").strip()
    aes = AESUtils(key=key, iv=iv)
    plaintext = aes.decrypt(ciphertext_hex)
    args.output.write_text(plaintext, encoding="utf-8")
    print(success(f"Wrote plaintext to {color(str(args.output), fg='bright_green')}"))


if __name__ == "__main__":
    main()
