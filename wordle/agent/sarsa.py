"""Sarsa Agent Module

This module implements a Reinforcement Learning-based agent that uses the Sarsa
algorithm to train and select actions.
"""

from .rl_base import BaseRLAgent


class SarsaAgent(BaseRLAgent):
    """The SarsaAgent is a Reinforcement Learning-based agent that implements
    the Sarsa learning algorithm:

    https://en.wikipedia.org/wiki/State%E2%80%93action%E2%80%93reward%E2%80%93state%E2%80%93action
    """
