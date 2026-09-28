from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path


@dataclass(slots=True)
class PPMImage:
    width: int
    height: int
    pixels: bytes

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")

        expected_size = self.width * self.height * 3
        if len(self.pixels) != expected_size:
            raise ValueError(
                f"pixel buffer has {len(self.pixels)} bytes, expected {expected_size}"
            )


def write_ppm(path: str | Path, image: PPMImage) -> None:
    output_path = Path(path)
    header = f"P6\n{image.width} {image.height}\n255\n".encode("ascii")

    with output_path.open("wb") as handle:
        handle.write(header)
        handle.write(image.pixels)


def read_ppm(path: str | Path) -> PPMImage:
    input_path = Path(path)

    with input_path.open("rb") as handle:
        magic = handle.readline().strip()
        if magic != b"P6":
            raise ValueError("unsupported PPM format; expected P6")

        dimensions = handle.readline().strip().split()
        if len(dimensions) != 2:
            raise ValueError("invalid PPM dimensions line")

        width, height = (int(value) for value in dimensions)

        max_value = handle.readline().strip()
        if max_value != b"255":
            raise ValueError("unsupported PPM max value; expected 255")

        pixels = handle.read()

    return PPMImage(width=width, height=height, pixels=pixels)


def image_from_rgb_bytes(rgb_bytes: bytes, width: int) -> PPMImage:
    if width <= 0:
        raise ValueError("width must be positive")

    if len(rgb_bytes) % 3 != 0:
        raise ValueError("rgb_bytes length must be divisible by 3")

    pixel_count = len(rgb_bytes) // 3
    height = max(1, ceil(pixel_count / width))
    padded_size = width * height * 3
    pixels = rgb_bytes.ljust(padded_size, b"\x00")
    return PPMImage(width=width, height=height, pixels=pixels)
