from __future__ import annotations


def bytes_to_rgb_bytes(data: bytes) -> tuple[bytes, int]:
    """Pad arbitrary bytes so they fit exactly into RGB triplets."""
    if not data:
        return b"", 0

    padding = (-len(data)) % 3
    return data + (b"\x00" * padding), padding


def rgb_bytes_to_bytes(rgb_bytes: bytes, original_length: int) -> bytes:
    if original_length < 0:
        raise ValueError("original_length must be non-negative")

    if len(rgb_bytes) % 3 != 0:
        raise ValueError("RGB byte stream must be divisible by 3")

    if original_length > len(rgb_bytes):
        raise ValueError("original_length cannot exceed decoded buffer length")

    return rgb_bytes[:original_length]


def pixel_count_for_bytes(byte_count: int) -> int:
    if byte_count < 0:
        raise ValueError("byte_count must be non-negative")

    if byte_count == 0:
        return 0

    return (byte_count + 2) // 3