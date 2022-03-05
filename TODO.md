# To-Do List for Project

- [ ] Learning Agent(s) Development
  - [ ] Decide on either one or two agents
  - [ ] Select set of actions for agents to choose from at each state
    - State 0-1 will eventually be limited to "best starting word" action, but
      that will depend on the learning.
    - Actions for 0-{2,3,4,5,6} might also use that action with a trimmed list
      to choose from.
    - Need minimum 4 selectable actions:
      - Random
      - Educated
      - Green-probability maximization
      - Heuristic(s)
  - [ ] Select heuristics
    - Need at least two
    - No more than two competing heuristics for one agent
    - If more than two are identified, make multiple agents
- [ ] Agent Training
  - [ ] Decide on train/test split for the 2315 answer words
  - [ ] Determine how to measure learning rates for RL agent(s)
- [ ] Testing/Evaluation
  - [ ] Translate learning rate data into graphs/charts
  - [ ] Final plot of performance against `SimpleAgent` and `RandomAgent`
