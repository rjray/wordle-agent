#!/usr/bin/env python

import os
import sys

_root_dir = os.path.dirname(__file__)
sys.path.append(_root_dir)

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from importlib import import_module
import matplotlib.pyplot as plt
import re

from wordle.game import Game
from wordle.utils import read_words

AGENTS_MAP = {
    "random": ["wordle.agent.random", "RandomAgent"],
    "simple": ["wordle.agent.simple", "SimpleAgent"],
}
"""A dictionary mapping command-line names of agent classes to the modules that
are dynamically imported."""

AGENTS_CODE = {}
"""A mapping of agent names to the dynamically-loaded classes."""

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
        action="append",
        help="Specific answer words, or a file name to use",
    )
    parser.add_argument(
        "--words",
        type=str,
        default=DEFAULT_WORDS,
        help="File name of allowed guess-words",
    )
    parser.add_argument(
        "-n", "--count", type=int, help="Solve only the first <count> words"
    )
    parser.add_argument(
        "-o", "--output", type=str,
        help="Name of file to write comparison data to"
    )
    parser.add_argument(
        "-s", "--stats", type=str, help="Name of file to write statistics to"
    )
    parser.add_argument(
        "-bc", "--bar-chart", type=str, help="Name of bar graph file to write"
    )
    parser.add_argument(
        "-p", "--plot", type=str, help="Name of file to write plot graph to"
    )
    parser.add_argument(
        "-r",
        "--runs",
        type=int,
        default=1,
        help="Number of complete runs to do for all agents",
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=os.cpu_count(),
        help="Maximum concurrent runs of agents",
    )
    parser.add_argument(
        "--show", action="store_true", help="If passed, dump data to stdout"
    )

    return vars(parser.parse_args())


def validate_data(data, run):
    if len(data) < 2:
        # Nothing to validate
        return

    basehist = data[0]["history"]
    for cmp in data[1:]:
        thisname = cmp["name"]
        thishist = cmp["history"]
        if len(thishist) != len(basehist):
            raise Exception(
                f"{thisname} (run {run}):  history length mismatch"
            )
        for i in range(len(basehist)):
            if basehist[i]["word"] != thishist[i]["word"]:
                raise Exception(f"{thisname} (run {run}): word {i} mismatch")

    return


def data2rows(data):
    rows = []
    row = ["index", "word"]
    for record in data:
        row.append(record["name"])

    rows.append(row)

    for i in range(len(data[0]["history"])):
        row = [i + 1, data[0]["history"][i]["word"]]
        for record in data:
            result = record["history"][i]["result"]
            guesses = len(record["history"][i]["guesses"])
            row.append(guesses if result == 1 else 0)

        rows.append(row)

    return rows


def write_csv_output(filename, rows):
    with open(filename, "w", newline="") as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerows(rows)

    return


def create_bar_chart(filename, rows):
    width = len(rows[0]) - 2
    labels = []
    values = []
    for i in range(width):
        labels.append(rows[0][i + 2])
        values.append([r[i + 2] for r in rows[1:]])

    _, ax = plt.subplots()

    words = [row[1] for row in rows[1:]]
    ax.bar(words, values[0], label=labels[0])
    for i in range(1, len(values)):
        ax.bar(words, values[i], label=labels[i], bottom=values[i - 1])

    if len(values) <= 25:
        plt.xticks(rotation=45, fontsize="small")
    else:
        ax.axes.xaxis.set_visible(False)

    ax.set_ylabel("Guesses")
    ax.set_title("Guesses by Word")
    ax.legend()

    plt.savefig(filename)


def create_plot(filename, runs):
    num_runs = len(runs)
    labels = [agent_result["name"] for agent_result in runs[0]]
    num_agents = len(labels)
    min_y = 0
    max_y = -30
    scores = [[] for _ in range(num_agents)]
    for i in range(num_agents):
        for run in runs:
            score = run[i]["score_avg"]
            if score > max_y:
                max_y = score
            if score < min_y:
                min_y = score
            scores[i].append(score)
    # import pprint
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(scores)

    _, ax = plt.subplots()

    ax.plot(range(1, num_runs + 1), scores[0], label=labels[0])
    for i in range(1, num_agents):
        ax.plot(range(1, num_runs + 1), scores[i], label=labels[i])

    ax.set(ylim=((min_y - 0.5), (max_y + 0.5)))
    ax.set_ylabel("Average Score")
    ax.set_title(f"Agent Scores Over {len(runs)} Runs")
    ax.legend()

    plt.savefig(filename)


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


def run_agent(agent, run, count):
    # Reset the agent prior to the run. For some agents, this introduces a
    # slight amount of extra stochastic nature.
    agent.reset()

    print(f"  Started:  agent {agent}, run {run+1}")
    result = agent.play(count)
    print(f"  Finished: agent {agent}, run {run+1}")
    return result


def main():
    args = parse_command_line()

    if args["max"] < 1:
        raise Exception("Cannot specify --max as less than 1")

    # Handle the answers/words arguments.
    words_list = read_words(args["words"])
    if not args["answers"]:
        answers_list = read_words(DEFAULT_ANSWERS)
    elif os.path.isfile(args["answers"][0]):
        answers_list = read_words(args["answers"][0])
    else:
        answers_list = ",".join(args["answers"]).split(",")
        if list(filter(lambda w: len(w) != 5, answers_list)):
            raise Exception("One or more words not 5 letters long")

    # Set up keyword arguments (if any) for the Game instances.
    game_args = {}
    if args["game"]:
        for pair in args["game"]:
            key, value = pair.split("=")
            if value in TF:
                value = TF[value]
            if re.match(value, r"^\d+$"):
                value = int(value)
            game_args[key] = value

    # Set up the agents.
    agents = []
    for agent_spec in args["agents"]:
        spec = agent_spec.split(",")
        agent_type = spec[0]
        agent_args = {}
        # This is a default identifying string, in case no name is given
        # agent_args["name"] = f"agent{len(agents)}"
        for pair in spec[1:]:
            key, value = pair.split("=")
            if value in TF:
                value = TF[value]
            if re.match(value, r"^\d+$"):
                value = int(value)
            agent_args[key] = value

        # Every agent gets a separate Game instance, in case of randomization.
        game = Game(answers_list, words_list, **game_args)
        agent = create_agent(agent_type, agent_args, game)

        agents.append(agent)

    # Run the agents, gathering the data.
    runs = args["runs"]
    run_results = [[None] * len(agents) for _ in range(runs)]
    print(f"Setting up {runs*len(agents)} total agent-runs")

    future_to_idx = {}
    with ProcessPoolExecutor(max_workers=args["max"]) as executor:
        for run in range(runs):
            for i, agent in enumerate(agents):
                future = executor.submit(run_agent, agent, run, args["count"])
                future_to_idx[future] = (i, run)

    for future in as_completed(future_to_idx):
        idx, run = future_to_idx[future]
        try:
            data = future.result()
        except Exception as e:
            print(f"{agents[idx]} (run {run}) threw exception: {e}")
        else:
            run_results[run][idx] = data

    # Handle validation and per-run actions.
    for run in range(runs):
        # First make sure that each agent ran the same words in the same
        # order.
        validate_data(run_results[run], run)

        # Produce CSV and/or bar chart output on a per-run basis:
        agent_rows = data2rows(run_results[run])
        if args["output"]:
            file = args["output"]
            if file.find("%d") >= 0:
                file = file % run
            print(f"  Writing {file}")
            write_csv_output(file, agent_rows)

        if args["bar_chart"]:
            file = args["bar_chart"]
            if file.find("%d") >= 0:
                file = file % run
            print(f"  Creating bar chart ({file})")
            create_bar_chart(file, agent_rows)

    # Process the full data.
    if args["plot"]:
        print(f"Creating plot ({args['plot']})")
        create_plot(args["plot"], run_results)

    if args["show"]:
        import pprint

        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(run_results)


if __name__ == "__main__":
    main()
