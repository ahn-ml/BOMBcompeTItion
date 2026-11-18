import numpy as np

from bombcompetition import DELTAS, RULES, Action, blast_cells, legal_actions


class Policy:
    """Wanders randomly but never steps into a bomb's range; sometimes drops a bomb."""

    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        if not obs["bombs"] and self.rng.random() < 0.1:
            return Action.BOMB
        danger = set().union(*(blast_cells(obs["walls"], b["pos"], RULES.radius) for b in obs["bombs"]))
        r, c = obs["me"]
        moves = [a for a in legal_actions(obs) if a != Action.BOMB]
        safe = [a for a in moves if (r + DELTAS[a][0], c + DELTAS[a][1]) not in danger]
        return int(self.rng.choice(safe or moves))
