"""Simple Agent Module

This module implements a very simple agent that has no learning. It simply
chooses words based on letter frequency from a list that is shortened by
filtering each iteration.
"""

from itertools import product
from operator import itemgetter

from .base import BaseAgent
from ..shared.words import letter_freq


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

    def __init__(self, game, words=None, *, name=None):
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

    def play_once(self):
        """Play a single word, creating and returning some data from the
        process (including the result)."""

        # Start by making a local copy of the words list.
        words = self.words.copy()
        result = {"guesses": [], "word": None, "result": 0, "score": 0.0}

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
                result["score"] += sum(score)

                # Have we found the word? A sum of 0 will mean that we have.
                if sum(score) == 0:
                    result["result"] = 1
                    result["word"] = guess
                    # Experimental: give a +5 rewards for solving
                    result["score"] += 5
                    break
                else:
                    # If we haven't found the word, trim the list down based on
                    # our guess and its score.
                    words = self.apply_guess(words, guess, score)

        if not result["word"]:
            # If we didn't find it within the given number of tries, mark it as
            # a "loss".
            result["word"] = self.game.word

        return result
