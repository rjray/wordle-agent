#!/bin/bash

./create_plots.py \
    --input results/agent_training-0.75-nr.csv \
    --input results/agent_training-0.90-nr.csv \
    --type poly3d \
    --field training_delta_rms \
    --max-samples 25 \
    --title "Sarsa vs. Q-Learning, ε fixed at 0.05 (reward=0)" \
    --label-agent-ticks \
    --data-set SarsaAgent-0.05-0.90-0.05 \
    --data-set QLearningAgent-0.05-0.90-0.05 \
    --data-set SarsaAgent-0.20-0.90-0.05 \
    --data-set QLearningAgent-0.20-0.90-0.05 \
    --data-set SarsaAgent-0.35-0.90-0.05 \
    --data-set QLearningAgent-0.35-0.90-0.05 \
    --data-set SarsaAgent-0.50-0.90-0.05 \
    --data-set QLearningAgent-0.50-0.90-0.05 \
    --output sarsa-q-poly3d-nr.png
