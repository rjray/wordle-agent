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

    def local_file(self, file):
        return file if os.path.isabs(file) else os.path.join(self.base, file)

    def create_letter_pos_probabilities(self, file):
        answers = self.game.answers
        ans_count = len(answers)
        base = ord("a")
        counters = [Counter() for _ in range(5)]
        fname = self.local_file(file)

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

    def load_letter_pos_probabilities(self, file):
        fname = self.local_file(file)

        with open(fname, "r") as f:
            data = json.load(f)

        return data


    def create_tglp_table(self, green_probabilities, file):
        tglp = {}
        base = ord("a")
        fname = self.local_file(file)

        for word in self.game.words:
            total = 0.0
            for i, ch in enumerate(word):
                total += green_probabilities[ord(ch) - base][i]

            tglp[word] = total

        with open(fname, "w") as f:
            json.dump(tglp, f, indent=2)

        return

    def load_tglp_probabilities(self, file):
        fname = self.local_file(file)

        with open(fname, "r") as f:
            data = json.load(f)

        return data
