#!/usr/bin/env python

import os
import sys

_root_dir = os.path.dirname(__file__)
sys.path.append(_root_dir)

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from importlib import import_module
import itertools
import re

from wordle.game import Game
from wordle.shared.datapoint import Datapoint, DATAPOINT_FIELDS
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

ALPHA_RANGE = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
EPSILON_RANGE = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]

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
        "-o",
        "--output",
        type=str,
        default="train_agents.csv",
        help="Name of CSV file for statistics"
    )
    parser.add_argument(
        "-tp",
        "--train-percent",
        type=int,
        default=TT_SPLIT,
        help=f"Training part of train/test split (default is {TT_SPLIT})"
    )
    parser.add_argument(
        "-d",
        "--data",
        type=str,
        default="./learning",
        help="Directory in which to write Q function data (./learning)"
    )

    return vars(parser.parse_args())


def write_csv_output(filename, rows):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(
            f, delimiter=",", fieldnames=DATAPOINT_FIELDS,
            quoting=csv.QUOTE_ALL
        )

        writer.writeheader()
        writer.writerows(rows)

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


def train_agent(agent, agent_id, train_pct, runs, pos, idx, total, dir):
    datapoints = []

    msg = f"\n{agent_id} starting ({agent} #{pos}, {idx+1} of {total})\n" + \
        f"\truns:    {runs}\n" + \
        f"\talpha:   {agent.alpha:.2f}\n" + \
        f"\tgamma:   {agent.gamma:.2f}\n" + \
        f"\tepsilon: {agent.epsilon:.2f}"
    print(msg)

    for run in range(runs):
        # Reset the agent prior to the run. For some agents, this introduces a
        # slight amount of extra stochastic nature.
        agent.reset()
        result = agent.train(train_pct)

        point = Datapoint(
            id=agent_id,
            agent=f"{agent}",
            alpha=agent.alpha,
            gamma=agent.gamma,
            epsilon=agent.epsilon,
            training_index=run,
            test_performance=result["testing_results"]["result"],
            num_states_visited=result["training_stats"]["states"],
            avg_visits_per_state=result["training_stats"]["avg_visits"],
            avg_score=result["testing_results"]["score_avg"],
            avg_guesses=result["testing_results"]["guess_avg"],
            training_delta_raw=result["learning_delta_raw"],
            training_delta_rms=result["learning_delta_rms"],
        )
        datapoints.append(point)

    print(f"\n{agent_id} finished")
    datafile = os.path.join(dir, agent_id + ".json")
    print(f"{agent_id} writing {agent_id + '.json'}")
    agent.Q.save(datafile)

    return datapoints


def main():
    args = parse_command_line()

    if args["max"] < 1:
        raise Exception("Cannot specify --max as less than 1")

    # Validate and set up the directory to write learning Q-function data to.
    dir = os.path.abspath(args["data"])
    if not os.path.isdir(dir):
        os.makedirs(dir, 0o755)

    # Handle the answers/words arguments.
    words_list = read_words(args["words"])
    answers_list = read_words(args["answers"])

    # Set up keyword arguments (if any) for the Game instances. Note that,
    # unlike the compare_agents script, here the default for Game instances is
    # to have "randomize" set to True.
    game_args = {"randomize": True}
    if args["game"]:
        gameargs = ",".join(args["game"]).split(",")
        for pair in gameargs:
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
            for epsilon in EPSILON_RANGE:
                for alpha in ALPHA_RANGE:
                    args_copy = agent_args.copy()
                    args_copy["alpha"] = alpha
                    args_copy["epsilon"] = epsilon
                    args_copy["gamma"] = 0.9
                    agents.append(create_agent(agent_type, args_copy, game))
    else:
        for spec in agent_specs:
            agents.append(create_agent(*spec))
    count_per_agent = int(len(agents) / len(agent_specs))

    # Spawn the training process for each agent in the agents list.
    tot = len(agents)
    pct = args["train_percent"]
    runs = args["runs"]
    run_results = [None] * tot
    msg = f"Setting up {tot} training runs, {runs} iterations each"
    if (args["spread"]):
        msg += " (spread-mode)"
    msg += "."
    print(msg)

    future_to_idx = {}
    with ProcessPoolExecutor(max_workers=args["max"]) as executor:
        for i, agent in enumerate(agents):
            pos = i % count_per_agent
            pos += 1
            agent_id = f"{agent}-{agent.alpha:.2f}-{agent.gamma:.2f}" + \
                f"-{agent.epsilon:.2f}"
            future = executor.submit(
                train_agent, agent, agent_id, pct, runs, pos, i, tot, dir
            )
            future_to_idx[future] = i

    for future in as_completed(future_to_idx):
        idx = future_to_idx[future]
        try:
            data = future.result()
        except Exception as e:
            run = int(idx % count_per_agent)
            run += 1
            msg = f"{agents[idx]} (run {run} of {count_per_agent}) threw " + \
                f"exception: {e}"
            print(msg)
        else:
            run_results[idx] = data

    # Now gather all the datapoints and write the output CSV file:
    rows = list(itertools.chain(*run_results))
    print(f"\nWriting {args['output']}")
    write_csv_output(args["output"], rows)


if __name__ == "__main__":
    main()
