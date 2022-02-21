"""Base Class for all Agent Classes

This provides BaseAgent, as well any common utility functions.
"""

from typing import List

from ..game import Game
from ..utils import read_words


class BaseAgent():
    def __init__(self, wordle: "Game", words: List[str] | str) -> None:
        self.game = wordle

        if isinstance(words, str):
            self.words = read_words(words)
        else:
            self.words = words.copy()
