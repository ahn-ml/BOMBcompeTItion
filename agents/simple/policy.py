import numpy as np

from bombcompetition import DELTAS, RULES, Action, blast_cells, parse


class Policy:
    """Wanders randomly but never steps into a bomb's range; sometimes drops a bomb."""

    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        view = parse(obs)
        if not view.bombs and self.rng.random() < 0.1:
            return Action.BOMB
        danger = set().union(*(blast_cells(view.walls, b, RULES.radius) for b in view.bombs))
        moves = [a for a in view.legal_actions() if a != Action.BOMB]
        safe = [a for a in moves if (view.me[0] + DELTAS[a][0], view.me[1] + DELTAS[a][1]) not in danger]
        return int(self.rng.choice(safe or moves))
