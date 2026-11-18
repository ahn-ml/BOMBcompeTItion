"""A weak but not suicidal baseline: random moves, but never step into a bomb's range.

Starting point for students: it shows how to use the observation for one simple rule.
"""

import numpy as np

STAY, UP, DOWN, LEFT, RIGHT, BOMB = range(6)
MOVES = {STAY: (0, 0), UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}
RADIUS = 2  # league rule: explosion length


def in_blast(walls, bomb, cell):
    """Is `cell` hit when the bomb at `bomb` explodes? (same row/col, within RADIUS, no wall between)"""
    (br, bc), (r, c) = bomb, cell
    if br != r and bc != c:
        return False
    dist = abs(br - r) + abs(bc - c)
    if dist > RADIUS:
        return False
    dr, dc = np.sign(r - br), np.sign(c - bc)
    return not any(walls[br + dr * k, bc + dc * k] for k in range(1, dist))


class Policy:
    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        walls = obs[0] > 0
        me = tuple(np.argwhere(obs[1])[0])
        opp = tuple(np.argwhere(obs[2])[0])
        bombs = [tuple(b) for b in np.argwhere((obs[3] > 0) | (obs[4] > 0))]

        def safe(cell):
            return not any(in_blast(walls, b, cell) for b in bombs)

        # cells I can step to this turn (or stay)
        options = []
        for a, (dr, dc) in MOVES.items():
            t = (me[0] + dr, me[1] + dc)
            if a == STAY or not (walls[t] or t in bombs or t == opp):
                options.append((a, t))

        safe_options = [a for a, t in options if safe(t)]
        if not bombs and self.rng.random() < 0.1:
            return BOMB
        if safe_options:
            return int(self.rng.choice(safe_options))
        return int(self.rng.choice([a for a, _ in options]))
