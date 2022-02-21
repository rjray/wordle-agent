"""Simple Agent Module

This module implements a very simple agent that has no learning. It simply
chooses words based on letter frequency from a list that is shortened by
filtering each iteration.
"""

from itertools import permutations
from typing import List

from .base import BaseAgent
from ..game import Game
from ..utils import letter_freq


class SimpleAgent(BaseAgent):
    def __init__(self, wordle: Game, words: List[str] | str) -> None:
        super().__init__(wordle, words)

        self.freq = letter_freq(self.words)

    def play(self, n: int = 0) -> List[dict]:
        history = []
        count = 0

        while self.game.start():
            count += 1
            if n > 0 and n < count:
                break

            history.append(self.play_once())

        score = sum(r.result for r in history) / len(history)

        return {"history": history, "count": len(history), "score": score}
