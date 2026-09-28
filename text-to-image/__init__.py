"""Core modules for the text-to-image pipeline."""

from .byte_codec import bytes_to_rgb_bytes, rgb_bytes_to_bytes
from .header import ChunkHeader, unpack_header
from .image_ppm import PPMImage, image_from_rgb_bytes, read_ppm, write_ppm
from .manifest import decode_manifest, encode_manifest, restore_manifest

__all__ = [
    "PPMImage",
    "ChunkHeader",
    "bytes_to_rgb_bytes",
    "decode_manifest",
    "encode_manifest",
    "image_from_rgb_bytes",
    "rgb_bytes_to_bytes",
    "read_ppm",
    "restore_manifest",
    "unpack_header",
    "write_ppm",
]