"""Base Class for all Agent Classes

This provides BaseAgent, the base class for other Agent implementations.
"""

from typing import List

from ..game import Game
from ..utils import read_words


class BaseAgent():
    """The BaseAgent class is a common base-class for the different agents that
    will be developed. It only provides very basic operations."""

    def __init__(self, game: Game, words: List[str] | str = None, *,
                 name: str) -> None:
        """Base constructor, to handle basic parts like handling the word list
        and the game instance.

        Positional parameters:

            game: An instance of the wordle.game.Game class
            words: The allowed (guessable) words, a list or a file name. If not
                   given, takes the list of words from the ``game`` parameter.
        
        Keyword parameters:

            name: An identifying string that will be incorporated into the
                  string representation of the object
        """
        self.game = game
        self.name = name

        if words:
            if isinstance(words, str):
                self.words = read_words(words)
            else:
                self.words = words.copy()
        else:
            self.words = game.words.copy()

    def __str__(self) -> str:
        """Provide a stringification of the object. If a ``name`` parameter
        was given at creation, include that."""
        if self.name:
            return f"{self.__class__.__name__}({self.name})"
        else:
            return self.__class__.__name__

    def reset(self) -> None:
        """Perform a reset of the agent. In the case of the base class, this
        only calls the ``reset`` method on the game object."""
        self.game.reset()
