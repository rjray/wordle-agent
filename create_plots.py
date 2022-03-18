#!/usr/bin/env python

import os
import sys

_root_dir = os.path.dirname(__file__)
sys.path.append(_root_dir)

import argparse
import csv
from matplotlib.collections import PolyCollection
import matplotlib.pyplot as plt
import numpy as np

from wordle.shared.datapoint import Datapoint

ALLOWED_FIELDS = [
    "train_performance",
    "test_performance",
    "num_states_visited",
    "avg_visits_per_state",
    "avg_score",
    "avg_guesses",
    "training_delta_raw",
    "training_delta_rms",
]

FIELD_LABELS = {
    "train_performance": "Training Performance %",
    "test_performance": "Testing Performance %",
    "num_states_visited": "Number of States Visited",
    "avg_visits_per_state": "Avg Visits Per State",
    "avg_score": "Average Score",
    "avg_guesses": "Average Guesses Taken",
    "training_delta_raw": "Total Training Delta",
    "training_delta_rms": "RMS of Training Delta",
}

FIELD_TRANSFORM = {
    "alpha": float,
    "gamma": float,
    "epsilon": float,
    "training_index": int,
    "train_performance": float,
    "test_performance": float,
    "num_states_visited": int,
    "avg_visits_per_state": float,
    "avg_score": float,
    "avg_guesses": float,
    "training_delta_raw": float,
    "training_delta_rms": float,
}


def parse_command_line(plot_types):
    parser = argparse.ArgumentParser()

    # Set up the arguments:
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        action="append",
        dest="inputs",
        required=True,
        help="Specify the CSV files to read for data"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Specify the file name to write plot to (defaults to <type>.png)"
    )
    parser.add_argument(
        "-ds",
        "--data-set",
        type=str,
        action="append",
        dest="datasets",
        nargs="*",
        help="Specify one or more data-set IDs to use"
    )
    parser.add_argument(
        "-ms",
        "--max-samples",
        type=int,
        help="Limit the number of samples per dataset (no default)"
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        choices=plot_types,
        help="Type of plot to create"
    )
    parser.add_argument(
        "-f",
        "--field",
        type=str,
        choices=ALLOWED_FIELDS,
        help="Data field to use for plot"
    )
    for axis in ["x", "y", "z"]:
        short = "-" + axis
        long = f"--{axis}-label"
        help = f"Label to use for the {axis.upper()} axis"
        parser.add_argument(short, long, type=str, help=help)
    parser.add_argument(
        "-lat",
        "--label-agent-ticks",
        action="store_true",
        help="If given, label Y-axis ticks with agent details"
    )

    return vars(parser.parse_args())


def fixup(dp):
    for field, transform in FIELD_TRANSFORM.items():
        dp[field] = transform(dp[field])

    return dp


def read_data(files):
    data = {}

    for file in files:
        with open(file, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                dp = fixup(Datapoint(**row))
                if row["id"] not in data:
                    data[row["id"]] = []
                data[row["id"]].append(dp)

    return data


def create_pairs(dataset):
    x = list(range(len(dataset)))

    return [(x[0], 0.0), *zip(x, dataset), (x[-1], 0.0)]


def make_triple(id):
    agent, alpha, gamma, epsilon = id.split("-")
    agent = agent.replace("Agent", "")

    return f"{agent}(α={alpha}, γ={gamma}, ε={epsilon})"


def create_poly3d_plot(
    datasets, *, field, output, x_label=None, y_label=None, z_label=None,
    max_samples, label_agent_ticks=False, **_
):
    if not x_label:
        x_label = "Training Iteration"
    if not y_label:
        y_label = r"Agent with parameters ($\alpha, \gamma, \epsilon$)"
    if not z_label:
        z_label = FIELD_LABELS[field]

    if max_samples:
        datasets = [ds[:max_samples] for ds in datasets]

    total_len = len(datasets[0])
    data = [[dp[field] for dp in ds] for ds in datasets]
    zs_list = range(1, len(data) + 1)
    all_data = sum(data, [])
    # data_min = min(all_data)
    data_max = max(all_data)
    # Make the pairs
    pairs = [create_pairs(ds) for ds in data]
    # Create the list of colors to use. Start with a dict indexed by the two
    # agent-names. These are done on reversed maps so they can be popped from.
    q_colors = list(plt.colormaps["Purples_r"](np.linspace(0, 0.5, len(data))))
    s_colors = list(plt.colormaps["Greens_r"](np.linspace(0, 0.5, len(data))))
    agent_colors = {
        "QLearningAgent": q_colors,
        "SarsaAgent": s_colors,
    }
    # Now interleave them based on the agent strings in the datasets.
    colors = [agent_colors[ds[0]["agent"]].pop() for ds in datasets]

    ax = plt.figure().add_subplot(projection='3d')
    # colors = plt.colormaps["viridis_r"](np.linspace(0, 1, len(data)))
    poly = PolyCollection(pairs, facecolors=colors, alpha=0.7)
    ax.add_collection3d(poly, zdir="y", zs=zs_list)
    ax.set(
        xlim=(0, total_len),
        ylim=(1, len(data) + 1),
        zlim=(0, data_max),
        xlabel=x_label,
        ylabel=y_label,
        zlabel=z_label
    )
    if label_agent_ticks:
        # Create the labels for the y-ticks
        yticklabels = [make_triple(ds[0]["id"]) for ds in datasets]
        ax.set_yticklabels(yticklabels, ha="left", fontsize=6.0)
        # Remove the Y-label, the ticks will overlap with it
        ax.set(ylabel="")

    plt.savefig(output)


def create_bar3d_plot(
    datasets, *, field, output, x_label=None, y_label=None, z_label=None,
    max_samples, **_
):
    if not x_label:
        x_label = "Training Iteration"
    if not y_label:
        y_label = r"Agent with parameters ($\alpha, \gamma, \epsilon$)"
    if not z_label:
        z_label = FIELD_LABELS[field]

    if max_samples:
        datasets = [ds[:max_samples] for ds in datasets]

    total_len = len(datasets[0])
    data = [[dp[field] for dp in ds] for ds in datasets]

    ax = plt.figure().add_subplot(projection='3d')
    colors = plt.colormaps["viridis_r"](np.linspace(0, 1, len(data)))

    for c, k in zip(colors, range(len(data))):
        xs = np.arange(total_len)
        ys = data[k]
        cs = [c] * total_len

        ax.bar(xs, ys, zs=k, zdir="y", color=cs, alpha=0.8)

    ax.set(
        xlabel=x_label,
        ylabel=y_label,
        zlabel=z_label
    )

    plt.savefig(output)


def main():
    # Set up the table of plot-types:
    plot_types = {
        "poly3d": create_poly3d_plot,
        "bar3d": create_bar3d_plot,
        "wire3d": None,
    }

    args = parse_command_line(sorted(list(plot_types.keys())))

    data = read_data(args["inputs"])

    # Flatten the nested-list structure that argparse made for "datasets":
    if args["datasets"]:
        args["datasets"] = sum(args["datasets"], [])

    # Now check for the "datasets" argument to have anything in it. If not,
    # show the list of available IDs.
    if not args["datasets"]:
        ids = list(data.keys())
        print("Available data-set IDs:")
        sets = "\n\t".join(sorted(ids))
        print(f"\n\t{sets}")
        exit(0)

    # Check for the required arguments that weren't explicitly tagged as
    # "required" because that would prevent the "datasets" trick from working:
    if not args["type"]:
        print("Argument --type must be given")
        exit(-1)
    if not args["field"]:
        print("Argument --field must be given")
        exit(-1)

    # Determine the file to write:
    if not args["output"]:
        args["output"] = f"{args['type']}.png"

    # Select the requested datasets:
    datasets = [data[dataset] for dataset in args["datasets"]]
    del args["datasets"]

    # Create the requested plot.
    plot_types[args["type"]](datasets, **args)

    exit(0)


if __name__ == "__main__":
    main()
