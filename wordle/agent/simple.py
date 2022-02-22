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
    return len(set(word))


def filter_out(words_in: set, guess: str, score: List[int]):
    words = list(words_in)

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

    return set(words)


class SimpleAgent(BaseAgent):
    def __init__(self, wordle: Game, words: List[str] | str = None, *,
                 seed: int = None) -> None:
        super().__init__(wordle, words)
        self.rng = Random(seed)

    def get_candidate_words(self, words: set) -> List[str]:
        if not words:
            return []

        candidates = []
        frequencies = letter_freq(list(words)).most_common()
        frequencies.reverse()
        letters = []
        # Set up the first 4 letters. The while-loop will cover adding new
        # letters.
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
            possibles = filter(lambda x: x in words, products)
            # Now further order it by words that have the most unique letters
            weighted = [(x, score(x)) for x in possibles]
            weighted.sort(key=itemgetter(1), reverse=True)
            candidates.extend([x for x, _ in weighted])
            if not frequencies:
                break

        return candidates

    def play_once(self):
        # Start by making a set object from the words list.
        words = set(self.words)
        result = {"guesses": [], "word": None, "result": 0}

        for round in range(6):
            word_list = self.get_candidate_words(words)
            if not word_list:
                print(f"Round {round+1}: have run out of candidate words.")
                break
            else:
                # guess = word_list[0]
                guess = self.rng.choice(word_list)
                score = self.game.guess(guess)
                result["guesses"].append((guess, score))
                if sum(score) == 10:
                    result["result"] = 1
                    result["word"] = guess
                    print(f"Guessed: {guess} ({round+1}/6)")
                    break
                else:
                    words = filter_out(words, guess, score)

        if not result["word"]:
            result["word"] = self.game.word
            print(f"Failed to guess: {self.game.word}")

        return result

    def play(self, n: int = 0) -> List[dict]:
        history = []
        count = 0

        while self.game.start():
            count += 1
            if n > 0 and n < count:
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
