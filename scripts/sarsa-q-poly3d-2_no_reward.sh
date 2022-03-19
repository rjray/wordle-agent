#!/bin/bash

./create_plots.py \
    --input results/agent_training-0.75-nr.csv \
    --input results/agent_training-0.90-nr.csv \
    --type poly3d \
    --field training_delta_rms \
    --max-samples 25 \
    --label-agent-ticks \
    --data-set SarsaAgent-0.05-0.90-0.05 \
    --data-set QLearningAgent-0.05-0.90-0.05 \
    --data-set SarsaAgent-0.05-0.90-0.20 \
    --data-set QLearningAgent-0.05-0.90-0.20 \
    --data-set SarsaAgent-0.05-0.90-0.35 \
    --data-set QLearningAgent-0.05-0.90-0.35 \
    --data-set SarsaAgent-0.05-0.90-0.50 \
    --data-set QLearningAgent-0.05-0.90-0.50 \
    --output sarsa-q-poly3d-2-nr.png
