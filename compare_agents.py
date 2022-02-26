#!/usr/bin/env python

import os, sys
_root_dir = os.path.dirname(__file__)
sys.path.append(_root_dir)

import argparse
import csv
from importlib import import_module
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor, as_completed
import re

from wordle.game import Game
from wordle.utils import read_words

AGENTS_MAP = {
    "random": ["wordle.agent.random", "RandomAgent"],
    "simple": ["wordle.agent.simple", "SimpleAgent"]
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
    parser.add_argument("-g", "--game-arguments", type=str, action="append",
                        dest="game",
                        help="Keyword arguments for the game constructor")
    parser.add_argument("-a", "--agent", type=str, action="append",
                        dest="agents", required=True,
                        help="Specifications of agents to run")
    parser.add_argument("--answers", type=str, action="append",
                        help="Specific answer words, or a file name to use")
    parser.add_argument("--words", type=str, default=DEFAULT_WORDS,
                        help="File name of allowed guess-words")
    parser.add_argument("-n", "--count", type=int,
                        help="Solve only the first <count> words")
    parser.add_argument("-o", "--output", type=str,
                        help="Name of file to write comparison data to")
    parser.add_argument("-s", "--stats", type=str,
                        help="Name of file to write statistics to")
    parser.add_argument("-bc", "--bar-chart", type=str,
                        help="Name of file to write bar graph to")
    parser.add_argument("-p", "--plot", type=str,
                        help="Name of file to write plot graph to")
    parser.add_argument("--show", action="store_true",
                        help="If passed, dump data to stdout")

    return vars(parser.parse_args())

def validate_data(data):
    if len(data) < 2:
        # Nothing to validate
        return

    basehist = data[0]["history"]
    for cmp in data[1:]:
        thisname = cmp["name"]
        thishist = cmp["history"]
        if len(thishist) != len(basehist):
            raise Exception(f"{thisname}:  history length mismatch")
        for i in range(len(basehist)):
            if basehist[i]["word"] != thishist[i]["word"]:
                raise Exception(f"{thisname}: word {i} mismatch")

    return

def data2rows(data):
    rows = []
    row = ["index", "word"]
    for record in data:
        row.append(record["name"])

    rows.append(row)

    for i in range(len(data[0]["history"])):
        row = [i+1, data[0]["history"][i]["word"]]
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
        labels.append(rows[0][i+2])
        values.append([r[i+2] for r in rows[1:]])

    _, ax = plt.subplots()

    words = [row[1] for row in rows[1:]]
    ax.bar(words, values[0], label=labels[0])
    for i in range(1, len(values)):
        ax.bar(words, values[i], label=labels[i],
               bottom=values[i-1])

    if len(values) <= 25:
        plt.xticks(rotation=45, fontsize="small")
    else:
        ax.axes.xaxis.set_visible(False)

    ax.set_ylabel("Guesses")
    ax.set_title("Guesses by Word")
    ax.legend()

    plt.savefig(filename)

def create_plot(filename, rows):
    width = len(rows[0]) - 2
    labels = []
    values = []
    for i in range(width):
        labels.append(rows[0][i+2])
        values.append([r[i+2] for r in rows[1:]])

    _, ax = plt.subplots()
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)

    ax.plot(values[0], label=labels[0])
    for i in range(1, len(values)):
        ax.plot(values[i], label=labels[i])

    ax.set(ylim=(-15, 15))
    ax.set_ylabel("Guesses")
    ax.set_title("Guesses by Word")
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

def run_agent(a, count):
    return a.play(count)

def main():
    args = parse_command_line()

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
            if re.match(value, "^\d+$"):
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
            if re.match(value, "^\d+$"):
                value = int(value)
            agent_args[key] = value

        # Every agent gets a separate Game instance, in case of randomization.
        game = Game(answers_list, words_list, **game_args)
        agent = create_agent(agent_type, agent_args, game)

        agents.append(agent)

    # Run the agents, gathering the data.
    agent_results = [None] * len(agents)
    print(f"Running {len(agents)} agents")
    with ProcessPoolExecutor(max_workers=8) as executor:
        future_to_idx = {executor.submit(run_agent, a, args["count"]): i
            for i, a in enumerate(agents)}
    for future in as_completed(future_to_idx):
        idx = future_to_idx[future]
        try:
            data = future.result()
        except Exception as e:
            print(f"{agents[idx].name} threw exception: {e}")
        else:
            agent_results[idx] = data
            print(f"Agent {data['name']} (index {idx}) completed")

    # Let's just make sure that each agent ran the same words in the same order.
    validate_data(agent_results)

    # Process the data.
    agent_rows = data2rows(agent_results)
    if args["output"]:
        print(f"Writing {args['output']}")
        write_csv_output(args["output"], agent_rows)

    if args["bar_chart"]:
        print(f"Creating bar chart ({args['bar_chart']})")
        create_bar_chart(args["bar_chart"], agent_rows)

    if args["plot"]:
        print(f"Creating plot ({args['plot']})")
        create_plot(args["plot"], agent_rows)

    if args["show"]:
        import pprint
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(agent_results)


if __name__ == '__main__':
    main()
