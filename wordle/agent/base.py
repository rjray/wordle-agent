"""Base Class for all Agent Classes

This provides BaseAgent, the base class for other Agent implementations.
"""

from typing import List

from ..game import Game
from ..utils import read_words


class BaseAgent():
    def __init__(self, wordle: "Game", words: List[str] | str = None) -> None:
        self.game = wordle

        if words:
            if isinstance(words, str):
                self.words = read_words(words)
            else:
                self.words = words.copy()
        else:
            self.words = wordle.words.copy()

    def reset(self) -> None:
        self.game.reset()
