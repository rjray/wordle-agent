"""Game Module

This module provides the basic game interface, stripped of most user-oriented
features. The idea is that the game-umpire is an instantiable class that will
play as many games as there are answer words.
"""

from collections import Counter
from random import shuffle
import sys
from typing import List

from .utils import read_words


class Game():
    """The Game class encapsulates the "umpire" of the game: an entity that
    governs the playing of the game and rules on each inputted word with
    regards to the game's current word. One instance of the Game class will
    play all 2315 game-words in sequence (or randomly), signalling when the
    list of game-words has been exhausted."""

    def __init__(self, answers: List[str] | str, words: List[str] | str, *,
                 random: bool = False) -> None:
        """Constructor. Takes two lists of words (either lists or filenames)
        and an optional ``random`` Boolean argument that governs whether the
        game-words are played in Wordle order or randomized."""

        if isinstance(words, str):
            self.words = set(read_words(words))
        else:
            self.words = words.copy()

        if isinstance(answers, str):
            self.answers = read_words(answers)
        else:
            self.answers = answers.copy()

        if random:
            shuffle(self.answers)

        self.index = 0
        self.guesses = 0
        self.word = None
        self.playing = False

    def start(self) -> bool:
        """Start a game on the next word in the list of answer-words. Returns a
        False value if there are no more words in the list."""

        if self.playing:
            print("WARNING: Starting next game while current one in progress",
                  file=sys.stderr)

        self.index += 1
        if self.index == len(self.answers):
            return False

        self.guesses = 0
        self.word = self.answers[self.index - 1]
        self.playing = True

        return True

    def guess(self, guess: str) -> List[int]:
        """Score the agent's guess, per Wordle rules. Returns a 5-element list
        of values in the range [0 .. 2], where:

            0: The letter is not present in the word at all
            1: The letter is present in the word but in the wrong place
            2: The letter is present and in the correct place

        Throws an error if not in an active game or if the guess is not in
        the list of allowed words."""

        if not self.playing:
            raise Exception("score_guess(): called with no active word")
        if len(guess) != 5:
            raise Exception(f"score_guess(): {guess} is not 5 letters")
        if guess not in self.words:
            raise Exception(f"score_guess(): {guess} is not an allowed guess")

        # If there have already been 6 guesses, return an empty list
        if self.guesses == 6:
            return []

        self.guesses += 1
        rtn = [0, 0, 0, 0, 0]
        counts = Counter(self.word)

        # Look for exact matches:
        for i, c in enumerate(self.word):
            if c == guess[i]:
                rtn[i] = 2
                counts[c] -= 1
        # Now count the right-letter-wrong-place matches:
        for i, c in enumerate(self.word):
            g = guess[i]
            if g == c:
                # We've already counted this as an exact match
                continue
            elif counts[g] > 0:
                rtn[i] = 1

        # If they've correctly guessed the word, flip self.playing to prevent
        # extra guessing.
        if guess == self.word:
            self.playing = False

        # Return the score.
        return rtn
