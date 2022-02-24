#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(__file__))

import argparse
import csv
from importlib import import_module
import matplotlib.pyplot as plt
from typing import Dict, List

from wordle.game import Game

AGENTS_MAP = {
    "random": ["wordle.agent.random", "RandomAgent"],
    "simple": ["wordle.agent.simple", "SimpleAgent"]
}
"""A dictionary mapping command-line names of agent classes to the modules that
are dynamically imported."""
AGENTS_CODE = {}

TF = {"True": True, "False": False}


def parse_command_line() -> Dict:
    parser = argparse.ArgumentParser()

    # Set up the arguments:
    parser.add_argument("-g", "--game-arguments", type=str, action="append",
                        dest="game",
                        help="Keyword arguments for the game constructor")
    parser.add_argument("-a", "--agent", type=str, action="append",
                        dest="agents", required=True,
                        help="Specifications of agents to run")
    parser.add_argument("--answers", type=str, action="append",
                        default="data/answers.txt",
                        help="Specific answer words, or a file name to use")
    parser.add_argument("--words", type=str, default="data/words.txt",
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

    return vars(parser.parse_args())

def validate_data(data: List[Dict]) -> None:
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

def data2rows(data: List[Dict]) -> List[List]:
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

def write_csv_output(filename: str, data: List[Dict]) -> None:
    rows = data2rows(data)

    with open(filename, "w", newline="") as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerows(rows)

    return

def create_bar_chart(filename: str, data: List[Dict]) -> None:
    rows = data2rows(data)

    labels = []
    values = []
    for i in range(len(data)):
        labels.append(data[i]["name"])
        values.append([r[i+2] for r in rows[1:]])

    _, ax = plt.subplots()
    ax.axes.xaxis.set_visible(False)

    ax.bar(range(1, len(rows)), values[0], label=labels[0])
    for i in range(1, len(values)):
        ax.bar(range(1, len(rows)), values[i], label=labels[i],
               bottom=values[i-1])

    ax.set_ylabel("Guesses")
    ax.set_title("Guesses by Word")
    ax.legend()

    plt.savefig(filename)

def create_plot(filename: str, data: List[Dict]) -> None:
    rows = data2rows(data)

    labels = []
    values = []
    for i in range(len(data)):
        labels.append(data[i]["name"])
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

def create_agent(type: str, args: Dict, game: Game):
    # Get the class to use:
    if type not in AGENTS_CODE:
        module_name, class_name = AGENTS_MAP[type]
        module = import_module(module_name)
        AGENTS_CODE[type] = getattr(module, class_name)

    handle = AGENTS_CODE[type]
    agent = handle(game, **args)

    return agent

def main():
    args = parse_command_line()

    game_args = {}
    if args["game"]:
        for pair in args["game"]:
            key, value = pair.split("=")
            if value in TF:
                value = TF[value]
            game_args[key] = value

    agents = []
    for agent_spec in args["agents"]:
        spec = agent_spec.split(",")
        agent_type = spec[0]
        if agent_type not in AGENTS_MAP:
            raise Exception(f"Unknown agent specification: {agent_type}")
        agent_args = {}
        # This is a default identifying string, in case no name is given
        # agent_args["name"] = f"agent{len(agents)}"
        for pair in spec[1:]:
            key, value = pair.split("=")
            if value in TF:
                value = TF[value]
            agent_args[key] = value

        # Every agent gets a separate Game instance, in case of randomization.
        game = Game(args["answers"], args["words"], **game_args)
        agent = create_agent(agent_type, agent_args, game)

        agents.append(agent)

    agent_results = []
    for a in agents:
        print(f"Running agent {a}")
        agent_result = a.play(args["count"])
        agent_results.append(agent_result)

    # import pprint
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(agent_results)

    validate_data(agent_results)

    # Process the data.
    if args["output"]:
        print(f"Writing {args['output']}")
        write_csv_output(args["output"], agent_results)

    if args["bar_chart"]:
        print(f"Creating bar chart ({args['bar_chart']})")
        create_bar_chart(args["bar_chart"], agent_results)

    if args["plot"]:
        print(f"Creating plot ({args['plot']})")
        create_plot(args["plot"], agent_results)


if __name__ == '__main__':
    main()
