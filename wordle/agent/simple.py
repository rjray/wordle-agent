"""Simple Agent Module

This module implements a very simple agent that has no learning. It simply
chooses words based on letter frequency from a list that is shortened by
filtering each iteration.
"""

from itertools import product
from operator import itemgetter

from .base import BaseAgent
from ..utils import letter_freq


def score(word: str):
    """Calculate a simple "score" for a word for the sake of sorting candidate
    guesses. For this agent, the score is just the number of distinct letters
    in the word. For example, "taste" has a score of 4 while "tears" has a
    score of 5."""

    return len(set(word))


class SimpleAgent(BaseAgent):
    """The SimpleAgent is a learning-free agent that plays based on a
    heuristic of always applying the result from the latest guess to reduce the
    pool of viable guesses. It essentially plays the game in "hard mode", even
    though the ``Game`` class doesn't enforce hard mode play."""

    def __init__(self, game, words = None, *, name = None):
        """Constructor for SimpleAgent. Just passes through to the superclass.

        Positional parameters:

            game: An instance of the wordle.game.Game class
            words: The allowed (guessable) words, a list or a file name. If not
                   given, the superclass constructor takes the list of words
                   from the ``game`` parameter.

        Keyword parameters:

            name: An identifying string to use in stringification of this
                  instance, to discern it from other instances
        """

        super().__init__(game, words, name=name)

    def apply_guess(self, words_in, guess, score):
        """Filter a new list of viable words based on the rules of this agent.
        For this agent, the filtering rules are essentially hard-mode playing.
        The list is winnowed down by applying simple logic around the letter
        scores from the guess.

        Parameters:

            words_in: A list of the current candidate words
            guess: The most-recent guess made by the agent
            score: The list of per-letter scores for the guess
        """

        words = words_in.copy()

        # First, get all the words that match letters in correct positions.
        include = [(guess[i], i) for i in range(5) if score[i] == 2]
        for ch, i in include:
            words = list(filter(lambda word: word[i] == ch, words))

        # Next, drop all words that contain a letter known to be completely
        # absent. Unless it matches a letter from the previous step, then don't
        # skip the word after all.
        keep = [ch for ch, _ in include]
        exclude = [guess[i] for i in range(5) if score[i] == 0]
        for ch in exclude:
            if ch not in keep:
                words = list(filter(lambda word: ch not in word, words))

        # Lastly, look for letters that must be present, but not in their
        # current position.
        present = [(guess[i], i) for i in range(5) if score[i] == 1]
        for ch, i in present:
            words = list(
                filter(lambda word: ch in word and word[i] != ch, words)
            )

        # In some cases, the actual guess-word can survive to this point. Make
        # sure it isn't in the new list.
        words_set = set(words)
        if guess in words_set:
            words.remove(guess)

        return words

    def select_guess(self, guesses):
        """Return a selected word from the list of possible guesses. For this
        agent, this sorts the list by uniqueness of letters and then picks the
        first in the resulting list."""

        # Order the potential guesses by the most unique letters
        weighted = [(x, score(x)) for x in guesses]
        weighted.sort(key=itemgetter(1), reverse=True)

        return weighted[0][0]

    def get_candidate_words(self, words):
        """Create a list of candidate words from the given set of words. Uses
        the frequency of the letters to find words that are created from the
        most-frequent letters possible."""

        if not words:
            return []

        candidates = []
        frequencies = letter_freq(words).most_common()
        frequencies.reverse()
        letters = []
        # Set up the first 4 letters (if there are 4). The while-loop will
        # cover adding new letters.
        for _ in range(4):
            if frequencies:
                letters.append(frequencies.pop()[0])

        while not candidates:
            # Add one more letter to the list (if there are any):
            if frequencies:
                letters.append(frequencies.pop()[0])
            # Use the Cartesian product fn from itertools to get all possible
            # permutations of letters with repetition.
            products = map(lambda x: "".join(x), product(letters, repeat=5))
            # Filter it down to acceptable Wordle guesses.
            word_set = set(words)
            possibles = filter(lambda x: x in word_set, products)
            candidates.extend(possibles)
            if not frequencies:
                break

        return candidates
