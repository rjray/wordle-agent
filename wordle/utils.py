"""Utils Module

Any code/functions common to both the game engine and the agent classes.
"""

from collections import Counter
from typing import List


def read_words(file: str) -> List[str]:
    """Read a specified words file into a list of words with the newlines
    stripped. Return the list."""
    with open(file, "r") as f:
        words = [line.strip() for line in f.readlines()]

    return words


def letter_freq(words: List[str]) -> Counter:
    """Computer the frequency of letters across the given list of words.
    Returns a ``Counter`` instance containing the counts."""
    c = Counter()

    for w in words:
        c += Counter(w)

    return c
