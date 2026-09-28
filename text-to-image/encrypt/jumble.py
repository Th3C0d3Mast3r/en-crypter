from __future__ import annotations


def jumble(encrypted_hex: str, jump: int) -> list[str]:
    if jump <= 0:
        raise ValueError("jump must be positive")

    groups = ["" for _ in range(jump)]
    for index, character in enumerate(encrypted_hex):
        groups[index % jump] += character
    return groups