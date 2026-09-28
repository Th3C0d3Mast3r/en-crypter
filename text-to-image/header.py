from __future__ import annotations

from dataclasses import dataclass
import struct
import zlib


MAGIC = b"TTI0"
VERSION = 1
HEADER_STRUCT = struct.Struct(">4sBBHIII")


@dataclass(slots=True)
class ChunkHeader:
    flags: int
    chunk_index: int
    total_chunks: int
    payload_length: int
    checksum: int

    def pack(self) -> bytes:
        return HEADER_STRUCT.pack(
            MAGIC,
            VERSION,
            self.flags,
            self.chunk_index,
            self.total_chunks,
            self.payload_length,
            self.checksum,
        )

    @classmethod
    def from_payload(
        cls,
        payload: bytes,
        *,
        flags: int = 0,
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> "ChunkHeader":
        return cls(
            flags=flags,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            payload_length=len(payload),
            checksum=zlib.crc32(payload) & 0xFFFFFFFF,
        )


def unpack_header(buffer: bytes) -> ChunkHeader:
    if len(buffer) < HEADER_STRUCT.size:
        raise ValueError("buffer is too small for a chunk header")

    magic, version, flags, chunk_index, total_chunks, payload_length, checksum = (
        HEADER_STRUCT.unpack_from(buffer)
    )

    if magic != MAGIC:
        raise ValueError("invalid chunk header magic")

    if version != VERSION:
        raise ValueError(f"unsupported chunk header version: {version}")

    return ChunkHeader(
        flags=flags,
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        payload_length=payload_length,
        checksum=checksum,
    )