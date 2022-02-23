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

    def play_once(self):
        """Play a single word, creating and returning some data from the
        process (including the result)."""

        # Start by making a local copy of the words list.
        words = self.words.copy()
        result = {"guesses": [], "word": None, "result": 0}

        for round in range(6):
            # For each of the 6 potential guesses, get a list of candidate
            # guesses from the current set of words. The get_candidate_words()
            # call will be increasingly smaller/shorter as words shrinks each
            # iteration.
            word_list = self.get_candidate_words(words)
            if not word_list:
                # This should not happen! But it has in the past, so...
                print(f"Round {round+1}: have run out of candidate words.")
                break
            else:
                guess = self.select_guess(word_list)

                # Have the game score our guess against the current word.
                score = self.game.guess(guess)
                result["guesses"].append((guess, score))

                # Have we found the word? 5 2's will mean that we have.
                if sum(score) == 10:
                    result["result"] = 1
                    result["word"] = guess
                    # print(f"Guessed: {guess} ({round+1}/6)")
                    break
                else:
                    # If we haven't found the word, trim the list down based on
                    # our guess and its score.
                    words = self.apply_guess(words, guess, score)

        if not result["word"]:
            # If we didn't find it within the given number of tries, mark it as
            # a "loss".
            result["word"] = self.game.word
            # print(f"Failed to guess: {self.game.word}")

        return result

    def play(self, n: int = None) -> List[dict]:
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

        score = sum(r["result"] for r in history) / len(history)
        guess_avg = sum(len(r["guesses"]) for r in history) / len(history)

        return {
            "name": f"{self}",
            "history": history,
            "count": len(history),
            "guess_avg": guess_avg,
            "score": score
        }
