#!/bin/bash

now=$(date '+%s')

./compare_agents.py \
    --agent simple \
    --agent random \
    --agent sarsa,file=learning-nr/SarsaAgent-0.05-0.90-0.05.json,tglp_table=data/training/common/tglp_table.json \
    --agent qlearning,file=learning-nr/QLearningAgent-0.05-0.90-0.05.json,tglp_table=data/training/common/tglp_table.json \
    --game-arguments randomize=True,seed=$now \
    --runs 100 \
    --max 4 \
    --plot runs-100x4-nr.png
