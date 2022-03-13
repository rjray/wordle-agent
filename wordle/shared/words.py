"""Words Module

Any code/functions common to multiple classes, that deals with words.
"""

from collections import Counter
from typing import List


def read_words(file: str):
    """Read a specified words file into a list of words with the newlines
    stripped. Return the list."""
    with open(file, "r") as f:
        words = [line.strip() for line in f.readlines()]

    return words


def letter_freq(words: List[str]):
    """Computer the frequency of letters across the given list of words.
    Returns a ``Counter`` instance containing the counts."""
    c = Counter()

    for w in words:
        c += Counter(w)

    return c


def score(word: str):
    """Calculate a simple "score" for a word for the sake of sorting candidate
    guesses. For this agent, the score is just the number of distinct letters
    in the word. For example, "taste" has a score of 4 while "tears" has a
    score of 5."""

    return len(set(word))
