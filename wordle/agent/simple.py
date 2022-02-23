"""Simple Agent Module

This module implements a very simple agent that has no learning. It simply
chooses words based on letter frequency from a list that is shortened by
filtering each iteration.
"""

from itertools import product
from operator import itemgetter
from random import Random
from typing import List

from .base import BaseAgent
from ..game import Game
from ..utils import letter_freq


def score(word: str):
    """Calculate a simple "score" for a word for the sake of sorting candidate
    guesses. For this agent, the score is just the number of distinct letters
    in the word. For example, "taste" has a score of 4 while "tears" has a
    score of 5."""

    return len(set(word))


def filter_out(words_in: List[str], guess: str, score: List[int]):
    """Filter a new list of viable words based on the rules of this agent. For
    this agent, the filtering rules are essentially hard-mode playing. The list
    is winnowed down by applying simple logic around the letter scores from the
    guess.

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

    # Next, drop all words that contain a letter known to be completely absent.
    # Unless it matches a letter from the previous step, then don't skip the
    # word after all.
    keep = [ch for ch, _ in include]
    exclude = [guess[i] for i in range(5) if score[i] == 0]
    for ch in exclude:
        if ch in keep:
            continue
        words = list(filter(lambda word: ch not in word, words))

    # Lastly, look for letters that must be present, but not in their current
    # position.
    present = [(guess[i], i) for i in range(5) if score[i] == 1]
    for ch, i in present:
        words = list(filter(lambda word: ch in word and word[i] != ch, words))

    return words


class SimpleAgent(BaseAgent):
    """The SimpleAgent is a learning-free agent that plays based on a
    heuristic of always applying the result from the latest guess to reduce the
    pool of viable guesses. It essentially plays the game in "hard mode", even
    though the ``Game`` class doesn't enforce hard mode play."""

    def __init__(self, game: Game, words: List[str] | str = None, *,
                 randomize: bool = True, seed: int = None) -> None:
        """Constructor for SimpleAgent. Handles the specific parameters
        ``randomize`` and ``seed`` which are not recognized by ``BaseAgent``.

        Parameters:

            game: An instance of the wordle.game.Game class
            words: The allowed (guessable) words, a list or a file name. If not
                   given, the superclass constructor takes the list of words
                   from the ``game`` parameter.
            randomize: A keyword Boolean parameter, whether to use randomness
                       in selecting each guess
            seed: A specific seed value to use for the localized random number
                  generator
        """

        super().__init__(game, words)
        self.randomize = randomize
        self.rng = Random(seed)

    def get_candidate_words(self, words: List[str]) -> List[str]:
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
            # Now further order it by words that have the most unique letters
            weighted = [(x, score(x)) for x in possibles]
            weighted.sort(key=itemgetter(1), reverse=True)
            candidates.extend([x for x, _ in weighted])
            if not frequencies:
                break

        return candidates

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
                # Select the guess based on whether randomize is set or not:
                if self.randomize:
                    guess = self.rng.choice(word_list)
                else:
                    guess = word_list[0]

                # Have the game score our guess against the current word.
                score = self.game.guess(guess)
                result["guesses"].append((guess, score))

                # Have we found the word? 5 2's will mean that we have.
                if sum(score) == 10:
                    result["result"] = 1
                    result["word"] = guess
                    print(f"Guessed: {guess} ({round+1}/6)")
                    break
                else:
                    # If we haven't found the word, trim the list down based on
                    # our guess and its score.
                    words = filter_out(words, guess, score)

        if not result["word"]:
            # If we didn't find it within the given number of tries, mark it as
            # a "loss".
            result["word"] = self.game.word
            print(f"Failed to guess: {self.game.word}")

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
            "history": history,
            "count": len(history),
            "guess_avg": guess_avg,
            "score": score
        }
