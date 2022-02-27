"""Trainer Module

This module contains the functions used to generate data for use in training
learning agents.
"""

from collections import Counter
import json
import os.path

from ..game import Game


class Trainer():
    def __init__(self, game: Game, base = "."):
        self.game = game
        self.base = base

    def create_letter_pos_probabilities(self, file):
        answers = self.game.answers
        ans_count = len(answers)
        base = ord("a")
        counters = [Counter() for _ in range(5)]
        fname = file if os.path.isabs(file) else os.path.join(self.base, file)

        for word in answers:
            for i, c in enumerate(word):
                counters[i][c] += 1

        probabilities = [[0] * 5 for _ in range(26)]
        for i, counter in enumerate(counters):
            for ch, count in counter.items():
                probabilities[ord(ch) - base][i] = count / ans_count

        with open(fname, "w") as f:
            json.dump(probabilities, f, indent=2)

        return
