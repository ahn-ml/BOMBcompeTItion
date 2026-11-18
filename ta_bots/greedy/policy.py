"""TA reference bot (keep out of the student release; stronger than examples/simple):
1. standing in a bomb's range: walk to the closest safe cell;
2. opponent in my blast range and I can still get away: drop a bomb;
3. otherwise walk toward the opponent without stepping into danger.
Bomb timing is ignored: every cell a bomb can reach counts as dangerous."""

from collections import deque

import numpy as np

from bombcompetition import DELTAS, MOVES, RULES, Action, blast_cells, parse


def shortest_paths(walls, start, blocked):
    """BFS from start. Returns {cell: (distance, first action on the way)}."""
    seen = {start: (0, Action.STAY)}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        dist, first = seen[cell]
        for a in MOVES:
            t = (cell[0] + DELTAS[a][0], cell[1] + DELTAS[a][1])
            if walls[t] or t in blocked or t in seen:
                continue
            seen[t] = (dist + 1, first if dist else a)
            queue.append(t)
    return seen


class Policy:
    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        view = parse(obs)
        bombs = set(view.bombs)
        danger = set().union(*(blast_cells(view.walls, b, RULES.radius) for b in bombs))
        paths = shortest_paths(view.walls, view.me, bombs | {view.opp})

        if view.me in danger:
            safe = [(d, a) for cell, (d, a) in paths.items() if cell not in danger]
            return int(min(safe)[1]) if safe else Action.STAY

        my_blast = blast_cells(view.walls, view.me, RULES.radius)
        if len(view.my_bombs) < RULES.max_bombs and view.opp in my_blast:
            after = danger | my_blast
            if any(cell not in after and d < RULES.fuse for cell, (d, _) in paths.items()):
                return Action.BOMB

        to_opp = shortest_paths(view.walls, view.opp, bombs)
        best, best_dist = Action.STAY, to_opp.get(view.me, (99,))[0]
        moves = list(MOVES)
        self.rng.shuffle(moves)
        for a in moves:
            t = (view.me[0] + DELTAS[a][0], view.me[1] + DELTAS[a][1])
            if t in to_opp and t not in danger and t not in bombs and to_opp[t][0] < best_dist:
                best, best_dist = a, to_opp[t][0]
        return int(best)
