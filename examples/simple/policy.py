"""A weak baseline: wander randomly, but never step into a bomb's blast range.
Sometimes drops a bomb when there is none on the board."""

import numpy as np

from bombcompetition import DELTAS, MOVES, RULES, Action, blast_cells, parse


class Policy:
    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs: np.ndarray) -> int:
        view = parse(obs)
        if not view.bombs and self.rng.random() < 0.1:
            return Action.BOMB

        danger = set()
        for bomb in view.bombs:
            danger |= blast_cells(view.walls, bomb, RULES.radius)

        options = [Action.STAY] + [a for a in MOVES if view.can_move(a)]
        safe = [a for a in options if (view.me[0] + DELTAS[a][0], view.me[1] + DELTAS[a][1]) not in danger]
        return int(self.rng.choice(safe or options))
