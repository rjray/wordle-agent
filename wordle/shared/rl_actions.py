"""Reinforcement Learning Actions Module

This module provides the actions that are taken by the reinforcement learning
agents based on their derived policies.
"""

import random


def guess_by_random(agent, words):
    """A word-selection action that simply chooses a word from the given list
    of words at random, using `random.choice()`.

    Parameters:

        `agent`: An instance of an agent class that derives from `BaseRLAgent`
        `words`: The list of words to choose from
    """
    guess = random.choice(words)
    agent.guesses.append(guess)

    return guess


def guess_by_tglp(agent, words):
    """A word-selection action that ranks the available words by their TGLP
    scores and picks from the resulting list.

    Parameters:

        `agent`: An instance of an agent class that derives from `BaseRLAgent`
        `words`: The list of words to choose from
    """

    tglp = agent.tglp_table
    choices = []

    for word in words:
        choices.append((word, tglp[word]))

    choices.sort(key=lambda x: x[1], reverse=True)
    guess = choices[0][0]
    agent.guesses.append(guess)

    return guess
