from __future__ import annotations

from math import ceil


def max_payload_for_image(width: int, height: int, header_size: int) -> int:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")

    capacity = width * height * 3
    payload_capacity = capacity - header_size
    if payload_capacity <= 0:
        raise ValueError("image capacity must be larger than header size")

    return payload_capacity


def chunk_payload(payload: bytes, width: int, height: int, header_size: int) -> list[bytes]:
    payload_capacity = max_payload_for_image(width, height, header_size)
    if not payload:
        return [b""]

    chunk_count = ceil(len(payload) / payload_capacity)
    return [
        payload[index * payload_capacity : (index + 1) * payload_capacity]
        for index in range(chunk_count)
    ]