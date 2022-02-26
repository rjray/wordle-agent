"""Utils Module

Any code/functions common to both the game engine and the agent classes.
"""

from collections import Counter


def read_words(file):
    """Read a specified words file into a list of words with the newlines
    stripped. Return the list."""
    with open(file, "r") as f:
        words = [line.strip() for line in f.readlines()]

    return words


def letter_freq(words):
    """Computer the frequency of letters across the given list of words.
    Returns a ``Counter`` instance containing the counts."""
    c = Counter()

    for w in words:
        c += Counter(w)

    return c
