from __future__ import annotations


def _group_length(total_length: int, jump: int, index: int) -> int:
    if index >= total_length:
        return 0
    return ((total_length - 1 - index) // jump) + 1


def reverse_jumble(jumbled_text: str, jump: int) -> str:
    if jump <= 0:
        raise ValueError("jump must be positive")

    lengths = [_group_length(len(jumbled_text), jump, index) for index in range(jump)]
    groups: list[str] = []
    cursor = 0
    for length in lengths:
        groups.append(jumbled_text[cursor : cursor + length])
        cursor += length

    characters: list[str] = []
    max_length = max(lengths, default=0)
    for offset in range(max_length):
        for group in groups:
            if offset < len(group):
                characters.append(group[offset])
    return "".join(characters)