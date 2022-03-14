#!/usr/bin/env python

import os
import sys

_root_dir = os.path.dirname(__file__)
sys.path.append(_root_dir)

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from importlib import import_module
import re

from wordle.game import Game
from wordle.shared.words import read_words

AGENTS_MAP = {
    "sarsa": ["wordle.agent.sarsa", "SarsaAgent"],
    "qlearning": ["wordle.agent.qlearning", "QLearningAgent"],
}
"""A dictionary mapping command-line names of agent classes to the modules that
are dynamically imported."""

AGENTS_CODE = {}
"""A mapping of agent names to the dynamically-loaded classes."""

TT_SPLIT = 75
"""The default training/testing split, training percentage."""

TF = {"True": True, "False": False}
DEFAULT_ANSWERS = os.path.join(_root_dir, "data/answers.txt")
DEFAULT_WORDS = os.path.join(_root_dir, "data/words.txt")


def parse_command_line():
    parser = argparse.ArgumentParser()

    # Set up the arguments:
    parser.add_argument(
        "-g",
        "--game-arguments",
        type=str,
        action="append",
        dest="game",
        help="Keyword arguments for the game constructor",
    )
    parser.add_argument(
        "-a",
        "--agent",
        type=str,
        action="append",
        dest="agents",
        required=True,
        help="Specifications of agents to run",
    )
    parser.add_argument(
        "--answers",
        type=str,
        default=DEFAULT_ANSWERS,
        help="File name of answer words to use",
    )
    parser.add_argument(
        "--words",
        type=str,
        default=DEFAULT_WORDS,
        help="File name of allowed guess-words",
    )
    parser.add_argument(
        "-r",
        "--runs",
        type=int,
        default=1,
        help="Number of complete runs to do for all agents/specs",
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=os.cpu_count(),
        help=f"Maximum concurrent runs of agents (default {os.cpu_count()})",
    )
    parser.add_argument(
        "--spread",
        action="store_true",
        help="If given, run all specified agents on the 10x10 spread"
    )
    parser.add_argument(
        "-s", "--stats", type=str, help="Name of CSV file for statistics"
    )
    parser.add_argument(
        "-tp",
        "--train-percent",
        type=int,
        default=TT_SPLIT,
        help=f"Training part of train/test split (default is {TT_SPLIT})"
    )

    return vars(parser.parse_args())


def write_csv_output(filename, rows, labels=None):
    with open(filename, "w", newline="") as f:
        csv_writer = csv.writer(f, delimiter=",")

        if labels:
            csv_writer.writerow(labels)

        csv_writer.writerows(rows)

    return


def create_agent(type, args, game):
    # Get the class to use:
    if type not in AGENTS_CODE:
        if type not in AGENTS_MAP:
            raise Exception(f"Unknown agent specification: {type}")
        module_name, class_name = AGENTS_MAP[type]
        module = import_module(module_name)
        AGENTS_CODE[type] = getattr(module, class_name)

    handle = AGENTS_CODE[type]
    agent = handle(game, **args)

    return agent


def train_agent(agent, runs):
    pass


def main():
    args = parse_command_line()

    if args["max"] < 1:
        raise Exception("Cannot specify --max as less than 1")

    # Handle the answers/words arguments.
    words_list = read_words(args["words"])
    answers_list = read_words(args["answers"])

    # Set up keyword arguments (if any) for the Game instances. Note that,
    # unlike the compare_agents script, here the default for Game instances is
    # to have "randomize" set to True.
    game_args = {"randomize": True}
    if args["game"]:
        for pair in args["game"]:
            key, value = pair.split("=")
            if value in TF:
                value = TF[value]
            elif re.match(r"^\d+$", value):
                value = int(value)
            game_args[key] = value

    # Set up the agents.
    agent_specs = []
    for agent_spec in args["agents"]:
        spec = agent_spec.split(",")
        agent_type = spec[0]
        agent_args = {}

        for pair in spec[1:]:
            key, value = pair.split("=")
            if value in TF:
                value = TF[value]
            elif re.match(r"^\d+$", value):
                value = int(value)
            elif re.match(r"^[-+]?[0-9]*[.]?[0-9]+$", value):
                value = float(value)
            agent_args[key] = value

        # Every agent gets a separate Game instance, in case of randomization.
        game = Game(answers_list, words_list, **game_args)
        agent_specs.append((agent_type, agent_args, game))

    # Now, if args["spread"] was given, we'll create 100 agents per agent-spec.
    # Otherwise, each spec will create just one agent.
    agents = []
    if args["spread"]:
        for agent_type, agent_args, game in agent_specs:
            for epsilon in range(1, 11):
                for alpha in range(1, 11):
                    args_copy = agent_args.copy()
                    args_copy["alpha"] = alpha * 0.05
                    args_copy["epsilon"] = epsilon * 0.05
                    args_copy["gamma"] = 0.9
                    agents.append(create_agent(agent_type, args_copy, game))
    else:
        for spec in agent_specs:
            agents.append(create_agent(*spec))
    count_per_agent = len(agents) / len(agent_specs)

    # Spawn the training process for each agent in the agents list.
    runs = args["runs"]
    run_results = [None] * len(agents)
    msg = f"Setting up {len(agents)} training runs, {runs} iterations " + \
        "each"
    if (args["spread"]):
        msg += " (spread-mode)"
    msg += "."
    print(msg)

    future_to_idx = {}
    with ProcessPoolExecutor(max_workers=args["max"]) as executor:
        for i, agent in enumerate(agents):
            future = executor.submit(train_agent, agent, runs)
            future_to_idx[future] = i

    for future in as_completed(future_to_idx):
        idx = future_to_idx[future]
        run = idx % count_per_agent
        run += 1
        try:
            data = future.result()
        except Exception as e:
            msg = f"{agents[idx]} (run {run} of {count_per_agent}) threw " + \
                f"exception: {e}"
            print(msg)
        else:
            run_results[run][idx] = data


if __name__ == "__main__":
    main()
