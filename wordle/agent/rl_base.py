"""Base Class for Reinforcement Learning Agents

This provides `BaseRLAgent`, which acts as the base class for the agents that
implement learning approaches.
"""

from .base import BaseAgent
from ..shared.rl_utils import Qsa
from ..shared.rl_actions import guess_by_random, guess_by_tglp, \
    guess_by_exploration
from ..training.trainer import Trainer

ACTION_TABLE = [
    guess_by_exploration,
    guess_by_tglp,
    guess_by_random,
]


class BaseRLAgent(BaseAgent):
    """The `BaseRLAgent` class is a common base-class for the classes that
    implement Reinforcement Learning approaches. It collects the common code
    between the `SarsaAgent` and `QLearningAgent` classes."""

    def __init__(
        self, game, words=None, *, name=None, Q=None, file=None,
        training=False, alpha=0.05, gamma=0.9, epsilon=0.05,
        action_table=ACTION_TABLE, letter_pos_probs=None, tglp_table=None
    ):
        """Constructor for Reinforcement Learning agents.

        Positional parameters:

            `game`: An instance of the `wordle.game.Game` class
            `words`: The allowed (guessable) words, a list or a file name. If
            not given, the superclass constructor takes the list of words
            from the `game` parameter.

        Keyword parameters:

            `name`: An identifying string to use in stringification of this
            instance, to discern it from other instances
            `Q`: An instance of `wordle.shared.rl_utils.Qsa` to use. If not
            given then a new instance is created.
            `file`: A file name from which to load an existing `Q(s,a)`
            function in place of creating a completely new `Qsa` instance.
            `training`: A Boolean value that indicates whether this object is
            created in training-mode or not. Defaults to `False` if `Q` or
            `file` are specified, `True` otherwise.
            `alpha`: The value for α, the step-size factor
            `gamma`: The value for γ, the discount factor
            `epsilon`: The value for ε, the learning-rate factor
            `action_table`: A list of actions that will be chosen from by the
            policy function in use
            `letter_pos_probs`: If given, either the name of a file that holds
            the table of probabilities by letter position, or the table itself.
            If not given, this is derived from `game`.
            `tglp_table`: If given, either the name of a file that holds a
            TGLP (Total Green-Letter Probability) table, or the table itself.
            If not given, this is derived from `game`.
        """

        super().__init__(game, words, name=name)

        # Not sure if I need to save this here or not. Might delete later.
        self.action_table = action_table

        # Set training. Generally False unless neither Q nor file were given.
        self.training = training
        if not training and not Q and not file:
            self.training = True

        # Create our Q function if it wasn't passed in as an argument.
        if not Q:
            Q = Qsa(num_actions=len(action_table), file=file)
        self.Q = Q
        self.file = file

        # Save the training parameters:
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

        # Create both policy functions:
        self.epsilon_greedy = self.Q.createEpsilonPolicy(epsilon)
        self.max_value = self.Q.createMaximizeValuePolicy()

        # Instance-level temporary values used on a per-word basis:
        self.guesses = []

        # Set up the positional probabilities and TGLP probabilities tables.

        # Need an instance of Trainer:
        trainer = Trainer(game)

        # Do the positional probabilities first, as they may be needed to
        # create the TGLP table.
        if not letter_pos_probs:
            self.letter_pos_probs = trainer.create_letter_pos()
        elif isinstance(letter_pos_probs, str):
            self.letter_pos_probs = trainer.load_letter_pos(letter_pos_probs)
        else:
            self.letter_pos_probs = letter_pos_probs

        # Read/create the TGLP table, as needed.
        if not tglp_table:
            self.tglp_table = trainer.create_tglp_table(self.letter_pos_probs)
        elif isinstance(tglp_table, str):
            self.tglp_table = trainer.load_tglp_table(tglp_table)
        else:
            self.tglp_table = tglp_table

        return

    def training_mode(self, train):
        """Explicitly set training-mode on or off, depending on the value of
        the Boolean `train` parameter."""

        self.training = train
        return

    def save_training(self, file):
        """Save the current state of the `Q` function to the specified `file`.
        """

        self.Q.save(file)
        return

    def train(self):
        """Train this agent instance based on the learning algorithm in the
        implementation class's `play_once()` method.

        Training is done by running the first 75% of the words while actively
        updating the Q function. Once this is done, the remaining 25% of words
        are run and the data gathered (as if from a "full" run) for evaluation
        of the agent.

        Note that this does not actively call `reset()` on the encapsulated
        `Game` instance, either before or after training. This is so that
        training data sequences remain predictable. An application running
        multiple trainings will need to reset the game between runs.

        The return value is a data structure that summarizes the learning and
        performance of the agent.
        """

        # First determine how many total answer-words there are, and draw the
        # 75/25 line. We only need train_words, as the game object will run
        # through the remainder for us automatically.
        train_words = int(len(self.game.answers) * 0.75)

        # Next, take a snapshot of Q before training so as to measure the
        # changes after training.
        pre_snapshot = self.Q.snapshot()

        self.training_mode(True)
        training_results = self.play(train_words)

        # Take another snapshot after the training:
        post_snapshot = self.Q.snapshot()
        # Also get the training stats from Q:
        training_stats = self.Q.statistics()

        # Now run the rest (in non-training mode) and gather data on that:
        self.training_mode(False)
        testing_results = self.play()

        learning_delta = self.calculate_delta(pre_snapshot, post_snapshot)

        return {
            "training_results": training_results,
            "testing_results": testing_results,
            "training_stats": training_stats,
            "learning_delta": learning_delta,
        }
