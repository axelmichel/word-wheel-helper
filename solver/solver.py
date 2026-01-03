from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable

ASCII_RE = re.compile(r"^[a-z]+$")


def load_base_words(dic_path: Path, encodings: list[str] | None = None) -> list[str]:
    """
    Loads base entries from a Hunspell .dic file:
    - tries encodings
    - skips count line if present
    - strips flags after '/'
    - lowercases
    - ASCII-only a-z
    - deduplicates
    """
    if encodings is None:
        encodings = ["utf-8", "latin-1", "cp1252"]

    lines: list[str] | None = None
    for enc in encodings:
        try:
            with dic_path.open("r", encoding=enc) as f:
                first = f.readline()
                rest = f.readlines()
            all_lines = rest if first.strip().isdigit() else [first] + rest
            lines = all_lines
            break
        except UnicodeDecodeError:
            continue

    if lines is None:
        # last resort: replace errors with the last encoding
        with dic_path.open("r", encoding=encodings[-1], errors="replace") as f:
            lines = f.readlines()

    words: set[str] = set()
    for line in lines:
        w = line.split("/", 1)[0].strip().lower()
        if ASCII_RE.fullmatch(w):
            words.add(w)

    return sorted(words)


def solve_candidates(allowed: str, mandatory: str, candidates: Iterable[str]) -> dict:
    """
    Pure solver:
    - allowed: 7 distinct letters
    - mandatory: 1 letter, must be in allowed
    - candidates: iterable of candidate words (already 'valid words' list)
    Returns dict with:
      - valid_words
      - pangrams_7_exact
      - longest_words
      - max_len
    """
    allowed = allowed.lower().strip()
    mandatory = mandatory.lower().strip()

    if len(allowed) != 7 or len(set(allowed)) != 7 or not ASCII_RE.fullmatch(allowed):
        raise ValueError("allowed must be exactly 7 distinct letters (a-z)")
    if len(mandatory) != 1 or not ASCII_RE.fullmatch(mandatory):
        raise ValueError("mandatory must be exactly one a-z letter")
    if mandatory not in allowed:
        raise ValueError("mandatory letter must be among allowed letters")

    allowed_set = set(allowed)
    allowed_counter = Counter(allowed)

    valid: list[str] = []
    pangrams: list[str] = []

    for w in candidates:
        w = w.strip().lower()
        if not w:
            continue
        if not ASCII_RE.fullmatch(w):
            continue
        if mandatory not in w:
            continue
        if set(w) - allowed_set:
            continue

        valid.append(w)
        if len(w) == 7 and Counter(w) == allowed_counter:
            pangrams.append(w)

    valid = sorted(set(valid), key=lambda x: (-len(x), x))
    pangrams = sorted(set(pangrams))

    max_len = len(valid[0]) if valid else 0
    longest = [w for w in valid if len(w) == max_len]

    return {
        "valid_words": valid,
        "pangrams_7_exact": pangrams,
        "longest_words": longest,
        "max_len": max_len,
    }