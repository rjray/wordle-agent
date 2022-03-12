"""Reinforcement Learning Utils Module

This module provides code that is shared between the various RL-based agents.
"""

from collections import defaultdict
import json
import numpy as np
from collections.abc import Callable


class Qsa(defaultdict):
    """The Qsa class implements the data structure that is used to represent
    the `Q(s,a)` function used in both Sarsa and Q-Learning. A Qsa instance
    will be able to handle the very basic functions, including saving and
    restoring to/from a file."""

    def __init__(self, *, num_actions: int, file: str = None) -> None:
        """Constructor. Build a Qsa object by first passing a specific factory
        function to the superclass constructor. Then, if `file` is given,
        attempt to load the Q(s,a) data from that file.

        Keyword parameters:

            `num_actions`: An integer specifying the number of actions that
            will be available at each state.
            `file`: If passed, a file name from which an existing Qsa table
            will be read.
        """

        super().__init__(lambda: np.zeros(num_actions))
        self.length = num_actions

        if file:
            self.load(file)

        return

    def load(self, file: str):
        """Load an existing Qsa representation from the given `file`, in JSON
        format. Clears out `self` before inserting new data, so any existing
        data will be lost."""

        with open(file, "r") as f:
            data = json.load(f)

            self.clear()
            for k, v in data.items():
                # Each key in the JSON data is the original tuple that has had
                # the numbers converted to strings, then all joined on ",".
                # This reverses that process.
                key = tuple(map(int, k.split(",")))
                # Likewise, the values in the JSON data are ordinary lists that
                # were converted from numpy arrays. Re-create them as np.array
                # instances.
                val = np.array(v)
                self[key] = val

        return self

    def save(self, file: str):
        """Save this instance to the given `file`, in JSON format. This requires
        conversion of both the tuples used as keys, and the `np.array`
        instances that are the values."""

        # We will "convert" this object into a plain dictionary:
        tmp = dict()

        for k, v in self.items():
            # Each key is a tuple, which can't be serialized in JSON as a key
            # for an object (dict) structure. So turn the numbers into a list
            # of strings and join them on ",".
            key = ",".join(map(str, k))
            # Each value is a np.array instance, which the JSON module cannot
            # serialize. Convert it to an ordinary list.
            val = list(v)
            tmp[key] = val

        with open(file, "w") as f:
            json.dump(tmp, f, indent=2)

        return self


def createEpsilonPolicy(Q: Qsa, epsilon: float) -> Callable[[tuple], int]:
    """Create an ε-greedy policy function based on the given `Q(s,a)` function
    (a `Qsa` instance) and value `epsilon`. The return value is a function that
    takes a state as input and returns the action-index for the action chosen
    randomly according to the ε-weighted selection."""

    def policy_fn(state):
        probabilities = np.ones(Q.length, dtype=float) * epsilon / Q.length
        best_action = np.argmax(Q[state])
        probabilities[best_action] += (1. - epsilon)

        return np.random.choice(Q.length, p=probabilities)

    return policy_fn


def createMaximizeValuePolicy(Q: Qsa) -> Callable[[tuple], int]:
    """Create a policy around the given `Q(s,a)` function (a `Qsa` instance)
    that always returns the action-index corresponding to the best value among
    the actions at the given state."""

    def policy_fn(state):
        return np.argmax(Q[state])

    return policy_fn
