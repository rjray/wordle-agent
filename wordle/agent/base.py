"""Base Class for all Agent Classes

This provides BaseAgent, the base class for other Agent implementations.
"""

from random import shuffle

from ..shared.words import read_words


class BaseAgent():
    """The BaseAgent class is a common base-class for the different agents that
    will be developed. It only provides very basic operations."""

    def __init__(self, game, words=None, *, name: str):
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

        shuffle(self.words)

    def __str__(self):
        """Provide a stringification of the object. If a ``name`` parameter
        was given at creation, include that."""
        if self.name:
            return f"{self.__class__.__name__}({self.name})"
        else:
            return self.__class__.__name__

    def reset(self):
        """Perform a reset of the agent. In the case of the base class, this
        calls the ``reset`` method on the game object and shuffles the internal
        copy of the word-list. The word-list is shuffled to introduce a slight
        variance in behavior of the ``SimpleAgent`` class."""
        shuffle(self.words)
        self.game.reset()

    def play_once(self):
        """Placeholder to throw an exception if an implementation class fails
        to define this method."""

        raise NotImplementedError(
            f"Class {self.__class__.__name__} has not defined play_once()"
        )

    def play(self, n):
        """Play the full game. Will run all the words provided as answers in
        the game object (based on how it was instantiated), unless the ``n``
        parameter is passed and is non-zero. If ``n`` is passed, only the first
        ``n`` words will be played.

        Returns a data structure of all the words played and some metrics over
        the full set."""

        history = []
        count = 0

        while self.game.start():
            count += 1
            if n and n < count:
                break

            history.append(self.play_once())

        result_total = 0
        guess_total = 0
        score_total = 0.0
        for outcome in history:
            result_total += outcome["result"]
            guess_total += len(outcome["guesses"])
            score_total += outcome["score"]

        count = len(history)
        result = result_total / count
        guess_avg = guess_total / count
        score_avg = score_total / count

        return {
            "name": f"{self}",
            "history": history,
            "count": len(history),
            "guess_avg": guess_avg,
            "score_avg": score_avg,
            "result": result
        }
