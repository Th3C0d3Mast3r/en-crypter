from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


NONCE_SIZE = 12
KEY_SIZE = 32


def generate_key() -> bytes:
    return AESGCM.generate_key(bit_length=KEY_SIZE * 8)


def encrypt_bytes(payload: bytes, key: bytes, *, associated_data: bytes | None = None) -> bytes:
    if len(key) != KEY_SIZE:
        raise ValueError("AES-256-GCM requires a 32-byte key")

    nonce = os.urandom(NONCE_SIZE)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, payload, associated_data)
    return nonce + ciphertext


def decrypt_bytes(payload: bytes, key: bytes, *, associated_data: bytes | None = None) -> bytes:
    if len(key) != KEY_SIZE:
        raise ValueError("AES-256-GCM requires a 32-byte key")

    if len(payload) <= NONCE_SIZE:
        raise ValueError("encrypted payload is too short")

    nonce = payload[:NONCE_SIZE]
    ciphertext = payload[NONCE_SIZE:]
    cipher = AESGCM(key)
    return cipher.decrypt(nonce, ciphertext, associated_data)