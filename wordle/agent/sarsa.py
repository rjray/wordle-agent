"""Sarsa Agent Module

This module implements a Reinforcement Learning-based agent that uses the Sarsa
algorithm to train and select actions.
"""

import numpy as np

from .rl_base import BaseRLAgent


class SarsaAgent(BaseRLAgent):
    """The SarsaAgent is a Reinforcement Learning-based agent that implements
    the Sarsa learning algorithm:

    https://en.wikipedia.org/wiki/State%E2%80%93action%E2%80%93reward%E2%80%93state%E2%80%93action
    """

    def play_once(self):
        """Play a single round (word) of the game. If `self.training` is `True`
        then update the Q function through each guess. Return the data gathered
        over this round in the same format as `SimpleAgent` returns."""

        # Start by making a local copy of the words list.
        words = self.words.copy()
        self.guesses.clear()
        result = {"guesses": [], "word": None, "result": 0,
                  "score": 0.0, "learning_delta": 0.0}
        # The starting state, within the simulation.
        state = (0,)
        # This is the function we'll use to determine actions.
        policy = self.epsilon_greedy if self.training else self.max_value
        # Start out by marking our start-state as visited.
        if self.training:
            self.Q.visit(state)

        # For Sarsa, we get the action before the start of the loop and will
        # update it within the loop as we do for state.
        action = policy(state)

        for round in range(6):
            guess = self.action_table[action](self, words)

            # Have the game score our guess against the current word.
            score = self.game.guess(guess)
            result["guesses"].append((guess, score))
            result["score"] += sum(score)
            next_state = tuple(score)

            # Calculate this guess's reward and next_state
            reward = sum(score)
            done = sum(score) == 0

            # Have we found the word? A sum of 0 will mean that we have.
            if done:
                result["result"] = 1
                result["word"] = guess
                # Experimental: give a +5 reward for solving
                result["score"] += 5
                reward += 5
            else:
                # If we haven't found the word, trim the list down based on
                # our guess and its score.
                words = self.apply_guess(words, guess, score)

            next_action = policy(next_state)

            # Perform the updating of Q if we're training:
            if self.training:
                td_target = \
                    reward + self.gamma * self.Q[next_state][next_action]
                td_delta = td_target - self.Q[state][action]
                self.Q[state][action] += self.alpha * td_delta
                result["learning_delta"] += abs(self.alpha * td_delta)
                # If training, track the visits to each state
                self.Q.visit(next_state)

            if done:
                break

            state = next_state
            action = next_action

        if not done:
            # If we didn't find it within the given number of tries, mark it as
            # a "loss".
            result["word"] = self.game.word

        return result
