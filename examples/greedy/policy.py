"""Rule-based baseline: escape danger, bomb when the opponent is in range, otherwise chase.

Uses only the observation. Danger ignores bomb timing (any cell a bomb can
reach counts as dangerous), which is simple but overly cautious.
"""

from collections import deque

import numpy as np

STAY, UP, DOWN, LEFT, RIGHT, BOMB = range(6)
MOVES = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}

# league rules
FUSE = 6
RADIUS = 2
MAX_BOMBS = 2


def blast_cells(walls, cell):
    r, c = cell
    cells = {cell}
    for dr, dc in MOVES.values():
        for k in range(1, RADIUS + 1):
            t = (r + dr * k, c + dc * k)
            if walls[t]:
                break
            cells.add(t)
    return cells


def bfs(walls, start, blocked):
    """Shortest paths from start. Returns {cell: (distance, first action)}."""
    seen = {start: (0, STAY)}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        d, first = seen[cell]
        for a, (dr, dc) in MOVES.items():
            t = (cell[0] + dr, cell[1] + dc)
            if walls[t] or t in blocked or t in seen:
                continue
            seen[t] = (d + 1, first if d else a)
            queue.append(t)
    return seen


class Policy:
    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        walls = obs[0] > 0
        me = tuple(int(x) for x in np.argwhere(obs[1])[0])
        opp = tuple(int(x) for x in np.argwhere(obs[2])[0])
        my_bombs = [tuple(int(x) for x in rc) for rc in np.argwhere(obs[3] > 0)]
        bombs = my_bombs + [tuple(int(x) for x in rc) for rc in np.argwhere(obs[4] > 0)]

        danger = set()
        for b in bombs:
            danger |= blast_cells(walls, b)
        paths = bfs(walls, me, set(bombs) | {opp})

        # 1. in danger: go to the closest safe cell
        if me in danger:
            safe = [(d, a) for cell, (d, a) in paths.items() if cell not in danger]
            return min(safe)[1] if safe else STAY

        # 2. opponent in my blast range and I can still get away: bomb
        if len(my_bombs) < MAX_BOMBS and opp in blast_cells(walls, me):
            after = danger | blast_cells(walls, me)
            if any(cell not in after and d < FUSE for cell, (d, _) in paths.items()):
                return BOMB

        # 3. walk toward the opponent without stepping into danger
        to_opp = bfs(walls, opp, set(bombs))
        best, best_d = STAY, to_opp.get(me, (99,))[0]
        options = list(MOVES.items())
        self.rng.shuffle(options)
        for a, (dr, dc) in options:
            t = (me[0] + dr, me[1] + dc)
            if t in to_opp and t not in danger and t not in bombs and to_opp[t][0] < best_d:
                best, best_d = a, to_opp[t][0]
        return best
