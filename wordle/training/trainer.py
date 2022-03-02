"""Trainer Module

This module contains the functions used to generate data for use in training
learning agents.
"""

from collections import Counter
import json
import os.path


def load_json(file):
    with open(file, "r") as f:
        data = json.load(f)

    return data


class Trainer():
    def __init__(self, game, base="."):
        self.game = game
        self.base = base

    def local_file(self, file):
        return file if os.path.isabs(file) else os.path.join(self.base, file)

    def create_letter_pos(self, file):
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

        return probabilities

    def load_letter_pos(self, file):
        return load_json(self.local_file(file))

    def create_tglp(self, green_probabilities, file):
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

        return tglp

    def load_tglp(self, file):
        return load_json(self.local_file(file))

    def create_all_files(self):
        letter_pos = self.create_letter_pos("letter_pos.json")
        self.create_tglp(letter_pos, "tglp_table.json")

        return

    def load_all_files(self):
        files = {}

        files["letter_pos"] = self.load_letter_pos("letter_pos.json")
        files["tglp_table"] = self.load_tglp("tglp_table.json")

        return files
