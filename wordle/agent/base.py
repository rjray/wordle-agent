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

            `game`: An instance of the wordle.game.Game class
            `words`: The allowed (guessable) words, a list or a file name. If
            not given, takes the list of words from the `game` parameter.

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
        """Provide a stringification of the object. If a `name` parameter
        was given at creation, include that."""
        if self.name:
            return f"{self.__class__.__name__}({self.name})"
        else:
            return self.__class__.__name__

    def reset(self):
        """Perform a reset of the agent. In the case of the base class, this
        calls the `reset` method on the game object and shuffles the internal
        copy of the word-list. The word-list is shuffled to introduce a slight
        variance in behavior of the `SimpleAgent` class."""
        shuffle(self.words)
        self.game.reset()

    def apply_guess(self, words_in, guess, score):
        """Filter a new list of viable words based on the rules of this agent.
        For most agents, the filtering rules are essentially hard-mode playing.
        The list is winnowed down by applying simple logic around the letter
        scores from the guess.

        Parameters:

            `words_in`: A list of the current candidate words
            `guess`: The most-recent guess made by the agent
            `score`: The list of per-letter scores for the guess
        """

        words = words_in.copy()

        # First, get all the words that match letters in correct positions.
        include = [(guess[i], i) for i in range(5) if score[i] == 0]
        for ch, i in include:
            words = list(filter(lambda word: word[i] == ch, words))

        # Next, look for letters that must be present, but not in their
        # current position.
        present = [(guess[i], i) for i in range(5) if score[i] == -0.5]
        for ch, i in present:
            words = list(
                filter(lambda word: ch in word and word[i] != ch, words)
            )

        # Lastly, drop all words that contain a letter known to be completely
        # absent. Unless it matches a letter from a previous step, then don't
        # skip the word after all.
        keep = set([ch for ch, _ in include])
        keep |= set([ch for ch, _ in present])
        exclude = [guess[i] for i in range(5) if score[i] == -1]
        for ch in exclude:
            if ch not in keep:
                words = list(filter(lambda word: ch not in word, words))

        # In some cases, the actual guess-word can survive to this point. Make
        # sure it isn't in the new list.
        words_set = set(words)
        if guess in words_set:
            words.remove(guess)

        return words

    def play_once(self):
        """Placeholder to throw an exception if an implementation class fails
        to define this method."""

        raise NotImplementedError(
            f"Class {self.__class__.__name__} has not defined play_once()"
        )

    def play(self, n):
        """Play the full game. Will run all the words provided as answers in
        the game object (based on how it was instantiated), unless the `n`
        parameter is passed and is non-zero. If `n` is passed, only the first
        `n` words will be played.

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
