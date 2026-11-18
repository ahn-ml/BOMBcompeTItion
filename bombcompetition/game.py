"""The game itself. One step = both players act at the same time:

1. Bomb: a player places a bomb on its own cell (at most `max_bombs` of its own at once).
2. Move: blocked by walls, bombs and the other player's current cell.
   If both players move into the same cell, neither moves.
3. Every bomb's fuse goes down by 1. At 0 it explodes in a cross of `radius`
   cells, stopped by walls, and sets off other bombs it reaches (chain).
   A player inside an explosion loses a life. It counts as a kill only when
   the other player's bomb was part of that explosion.
4. After a death both players go back to their start cells and bombs are cleared.

The game ends when a player has no lives left or after `max_steps`.
"""

from dataclasses import dataclass

import numpy as np

from .rules import DELTAS, RULES, Action, Rules

Cell = tuple[int, int]
N_CHANNELS = 9


def blast_cells(walls: np.ndarray, cell: Cell, radius: int) -> set[Cell]:
    """Cells hit by a bomb at `cell`: a cross of `radius` cells that stops at walls."""
    r, c = cell
    cells = {cell}
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        for k in range(1, radius + 1):
            t = (r + dr * k, c + dc * k)
            if walls[t]:
                break
            cells.add(t)
    return cells


@dataclass
class Bomb:
    owner: int
    fuse: int


@dataclass(frozen=True)
class Death:
    player: int
    killer: int | None  # the other player, or None for a suicide


class Game:
    """Two-player game. Players are 0 (A) and 1 (B). Positions are (row, col)."""

    def __init__(self, rules: Rules = RULES):
        rows = rules.rows
        self.size = len(rows)
        if any(len(row) != self.size for row in rows):
            raise ValueError("map must be square")
        self.walls = np.array([[ch == "#" for ch in row] for row in rows])
        if not (self.walls[0].all() and self.walls[-1].all() and self.walls[:, 0].all() and self.walls[:, -1].all()):
            raise ValueError("map border must be all walls")
        starts = rules.starts or [self._find(rows, ch) for ch in "AB"]
        self.starts = [tuple(s) for s in starts]
        if self.starts[0] == self.starts[1] or any(self.walls[s] for s in self.starts):
            raise ValueError(f"bad start cells {self.starts}")
        if rules.fuse < 1 or rules.radius < 0 or rules.max_bombs < 1 or rules.lives < 1:
            raise ValueError(f"bad rules {rules}")

        self.rules = rules
        self.lives = [rules.lives, rules.lives]
        self.kills = [0, 0]
        self.t = 0
        self.done = False
        self._new_round()

    @staticmethod
    def _find(rows, ch) -> Cell:
        for r, row in enumerate(rows):
            if ch in row:
                return (r, row.index(ch))
        raise ValueError(f"no '{ch}' start cell in the map")

    def _new_round(self):
        self.pos: list[Cell] = list(self.starts)
        self.bombs: dict[Cell, Bomb] = {}
        self.last_blast: set[Cell] = set()  # cells that exploded in the last step (for rendering)

    def step(self, a0: int, a1: int) -> list[Death]:
        """Advance one step with both players' actions. Returns who died this step."""
        if self.done:
            raise RuntimeError("game is over")
        actions = (Action(int(a0)), Action(int(a1)))

        for p, a in enumerate(actions):
            owned = sum(b.owner == p for b in self.bombs.values())
            if a == Action.BOMB and owned < self.rules.max_bombs and self.pos[p] not in self.bombs:
                self.bombs[self.pos[p]] = Bomb(p, self.rules.fuse)

        targets = [self._target(p, a) for p, a in enumerate(actions)]
        if targets[0] != targets[1]:
            self.pos = targets

        blast, hit_by = self._explode()
        deaths = []
        for p in (0, 1):
            if self.pos[p] in blast:
                killer = 1 - p if 1 - p in hit_by[p] else None
                deaths.append(Death(p, killer))
                self.lives[p] -= 1
                if killer is not None:
                    self.kills[killer] += 1

        self.t += 1
        self.done = min(self.lives) <= 0 or self.t >= self.rules.max_steps
        if deaths and not self.done:
            self._new_round()
        self.last_blast = blast
        return deaths

    def _target(self, p: int, a: Action) -> Cell:
        (r, c), (dr, dc) = self.pos[p], DELTAS[a]
        t = (r + dr, c + dc)
        if t == self.pos[p] or self.walls[t] or t in self.bombs or t == self.pos[1 - p]:
            return self.pos[p]
        return t

    def _explode(self) -> tuple[set[Cell], list[set[int]]]:
        """Tick all fuses and resolve (chained) explosions.
        Returns the exploded cells and, per player, the owners of the bombs that hit them."""
        for b in self.bombs.values():
            b.fuse -= 1
        blast: set[Cell] = set()
        hit_by: list[set[int]] = [set(), set()]
        queue = [cell for cell, b in self.bombs.items() if b.fuse <= 0]
        while queue:
            cell = queue.pop()
            bomb = self.bombs.pop(cell, None)
            if bomb is None:
                continue
            hit = blast_cells(self.walls, cell, self.rules.radius)
            blast |= hit
            queue += [x for x in hit if x in self.bombs]
            for p in (0, 1):
                if self.pos[p] in hit:
                    hit_by[p].add(bomb.owner)
        return blast, hit_by

    def winner(self) -> int | None:
        """The player with more lives left, or None for a draw."""
        if self.lives[0] == self.lives[1]:
            return None
        return 0 if self.lives[0] > self.lives[1] else 1

    def obs(self, p: int) -> np.ndarray:
        """Observation of player p, float32 (N_CHANNELS, size, size). Layout: bombcompetition/observation.py"""
        r = self.rules
        o = np.zeros((N_CHANNELS, self.size, self.size), dtype=np.float32)
        o[0] = self.walls
        o[1][self.pos[p]] = 1
        o[2][self.pos[1 - p]] = 1
        for cell, bomb in self.bombs.items():
            o[3 if bomb.owner == p else 4][cell] = bomb.fuse / r.fuse
        o[5] = self.lives[p] / r.lives
        o[6] = self.lives[1 - p] / r.lives
        o[7] = (r.max_steps - self.t) / r.max_steps
        o[8] = p
        return o
