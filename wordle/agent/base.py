"""Base Class for all Agent Classes

This provides BaseAgent, the base class for other Agent implementations.
"""

from typing import List

from ..game import Game
from ..utils import read_words


class BaseAgent():
    """The BaseAgent class is a common base-class for the different agents that
    will be developed. It only provides very basic operations."""

    def __init__(self, game: Game, words: List[str] | str = None) -> None:
        """Base constructor, to handle basic parts like handling the word list
        and the game instance.

        Parameters:

            game: An instance of the wordle.game.Game class
            words: The allowed (guessable) words, a list or a file name. If not
                   given, takes the list of words from the ``game`` parameter.
        """
        self.game = game

        if words:
            if isinstance(words, str):
                self.words = read_words(words)
            else:
                self.words = words.copy()
        else:
            self.words = game.words.copy()

    def reset(self) -> None:
        """Perform a reset of the agent. In the case of the base class, this
        only calls the ``reset`` method on the game object."""
        self.game.reset()
