"""Class for Agent Training Datapoints

This module provides the Datapoint class and some support values, used to
store and manipulate the data obtained from training sessions of the
learning-based agents.
"""

DATAPOINT_FIELDS = [
    "id",
    "agent",
    "alpha",
    "gamma",
    "epsilon",
    "training_index",
    "test_performance",
    "num_states_visited",
    "avg_visits_per_state",
    "avg_score",
    "avg_guesses",
    "training_delta_raw",
    "training_delta_rms",
]
"""An array that both lists the fields of a Datapoint and specifies their order
in the output CSV."""


class Datapoint(dict):
    """The Datapoint class..."""

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            self[k] = v

        missing = []
        for field in DATAPOINT_FIELDS:
            if field not in self:
                missing.append(field)
        if missing:
            raise Exception(f"Datapoint missing fields: {missing}")

        extra = []
        for field in self.keys():
            if field not in DATAPOINT_FIELDS:
                extra.append(field)
        if extra:
            raise Exception(f"Unknown Datapoint fields: {extra}")

        return
