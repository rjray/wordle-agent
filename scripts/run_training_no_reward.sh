#!/bin/bash

now=$(date '+%s')

./train_agents.py \
    --max 6 \
    --agent sarsa \
    --agent qlearning \
    --game-arguments randomize=True,seed=$now \
    --spread \
    --runs 50 \
    --reward 0 \
    --data ./learning-nr-tmp \
    --output agent_training-0.90-nr.csv

./train_agents.py \
    --max 6 \
    --agent sarsa \
    --agent qlearning \
    --game-arguments randomize=True,seed=$now \
    --spread \
    --runs 50 \
    --gamma 0.75 \
    --reward 0 \
    --data ./learning-nr-tmp \
    --output agent_training-0.75-nr.csv
