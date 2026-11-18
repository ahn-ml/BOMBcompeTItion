"""Rules and game engine.

Each step both players act at the same time:
1. BOMB drops a bomb on your cell (at most `max_bombs` of yours at once).
2. Moves are blocked by walls, bombs and the other player; two players moving into one cell both stay.
3. Fuses tick down. A bomb at 0 explodes in a cross of `radius` cells, stopped by walls,
   setting off other bombs it reaches. A player in the explosion loses a life; it is a kill
   for the opponent if the opponent's bomb was part of it.
4. After a death both players return to their start cells and all bombs are removed.
The game ends when someone has no lives left or after `max_steps`.
"""

from dataclasses import dataclass
from enum import IntEnum

import numpy as np

Cell = tuple[int, int]  # (row, col), row 0 is the top

MAP = (
    "#########",
    "#A..#...#",
    "#.#.#.#.#",
    "#.#...#.#",
    "#...#...#",
    "#.#...#.#",
    "#.#.#.#.#",
    "#...#..B#",
    "#########",
)


class Action(IntEnum):
    STAY = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    BOMB = 5


DELTAS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (0, 0))  # (d_row, d_col) per action
MOVES = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)


@dataclass(frozen=True)
class Rules:
    layout: tuple[str, ...] = MAP  # '#' wall, '.' floor, 'A'/'B' start cells; border must be walls
    starts: tuple[Cell, Cell] | None = None  # overrides the 'A'/'B' cells
    fuse: int = 6  # steps from dropping a bomb to its explosion
    radius: int = 2  # explosion reach in each direction
    max_bombs: int = 2  # bombs per player on the board at once
    lives: int = 3
    max_steps: int = 300


RULES = Rules()  # the official league rules


@dataclass
class Bomb:
    owner: int
    fuse: int


@dataclass(frozen=True)
class Death:
    player: int
    killer: int | None  # the opponent, or None for a suicide


def blast_cells(walls: np.ndarray, cell: Cell, radius: int) -> set[Cell]:
    """Cells hit by a bomb at `cell`."""
    cells = {cell}
    for dr, dc in DELTAS[1:5]:
        for k in range(1, radius + 1):
            t = (cell[0] + dr * k, cell[1] + dc * k)
            if walls[t]:
                break
            cells.add(t)
    return cells


class Game:
    """Players are 0 (A) and 1 (B)."""

    def __init__(self, rules: Rules = RULES):
        layout = rules.layout
        self.size = len(layout)
        self.walls = np.array([[ch == "#" for ch in row] for row in layout])
        find = {ch: (r, row.index(ch)) for r, row in enumerate(layout) for ch in "AB" if ch in row}
        self.starts = list(rules.starts or (find.get("A"), find.get("B")))
        if self.walls.shape != (self.size, self.size) or not (self.walls[[0, -1]].all() and self.walls[:, [0, -1]].all()):
            raise ValueError("the map must be square with walls all around")
        if None in self.starts or self.starts[0] == self.starts[1] or any(self.walls[s] for s in self.starts):
            raise ValueError(f"bad start cells: {self.starts}")

        self.rules = rules
        self.lives = [rules.lives, rules.lives]
        self.kills = [0, 0]
        self.t = 0
        self.done = False
        self._new_round()

    def _new_round(self):
        self.pos: list[Cell] = list(self.starts)
        self.bombs: dict[Cell, Bomb] = {}
        self.last_blast: set[Cell] = set()  # cells that exploded in the last step
        self.last_pos: list[Cell] = list(self.pos)  # positions at the end of the last step, before a new round

    def step(self, a0: int, a1: int) -> list[Death]:
        """Play one step and return who died in it."""
        if self.done:
            raise RuntimeError("the game is over")
        actions = (Action(a0), Action(a1))

        for p, a in enumerate(actions):
            mine = sum(b.owner == p for b in self.bombs.values())
            if a == Action.BOMB and mine < self.rules.max_bombs and self.pos[p] not in self.bombs:
                self.bombs[self.pos[p]] = Bomb(p, self.rules.fuse)

        targets = [self._target(p, a) for p, a in enumerate(actions)]
        if targets[0] != targets[1]:
            self.pos = targets

        blast, hit_by = self._explode()
        deaths = [Death(p, 1 - p if 1 - p in hit_by[p] else None) for p in (0, 1) if self.pos[p] in blast]
        for d in deaths:
            self.lives[d.player] -= 1
            if d.killer is not None:
                self.kills[d.killer] += 1

        self.t += 1
        self.done = min(self.lives) <= 0 or self.t >= self.rules.max_steps
        hit_pos = list(self.pos)
        if deaths and not self.done:
            self._new_round()
        self.last_blast, self.last_pos = blast, hit_pos
        return deaths

    def _target(self, p: int, a: Action) -> Cell:
        (r, c), (dr, dc) = self.pos[p], DELTAS[a]
        t = (r + dr, c + dc)
        blocked = self.walls[t] or t in self.bombs or t == self.pos[1 - p]
        return self.pos[p] if blocked and t != self.pos[p] else t

    def _explode(self) -> tuple[set[Cell], list[set[int]]]:
        """Tick fuses and resolve chained explosions.
        Returns the exploded cells and, per player, the owners of the bombs that reached them."""
        for b in self.bombs.values():
            b.fuse -= 1
        blast, hit_by = set(), [set(), set()]
        queue = [cell for cell, b in self.bombs.items() if b.fuse <= 0]
        while queue:
            cell = queue.pop()
            if (bomb := self.bombs.pop(cell, None)) is None:
                continue
            hit = blast_cells(self.walls, cell, self.rules.radius)
            blast |= hit
            queue += [x for x in hit if x in self.bombs]
            for p in (0, 1):
                if self.pos[p] in hit:
                    hit_by[p].add(bomb.owner)
        return blast, hit_by

    def winner(self) -> int | None:
        """The player with more lives left, None for a draw."""
        if self.lives[0] == self.lives[1]:
            return None
        return int(self.lives[1] > self.lives[0])

    def obs(self, p: int) -> dict:
        """What player p sees: the game state as it is."""
        return {
            "player": p,  # 0 = A, 1 = B
            "walls": self.walls.copy(),  # bool (size, size), walls[row, col]
            "me": self.pos[p],
            "opp": self.pos[1 - p],
            "bombs": tuple({"pos": cell, "owner": b.owner, "fuse": b.fuse} for cell, b in self.bombs.items()),
            "lives": (self.lives[p], self.lives[1 - p]),  # (mine, opponent's)
            "step": self.t,
        }


def legal_actions(obs: dict) -> list[Action]:
    """STAY, BOMB and the moves that are not blocked by a wall, a bomb or the opponent."""
    bombs = {b["pos"] for b in obs["bombs"]}
    moves = []
    for a in MOVES:
        t = (obs["me"][0] + DELTAS[a][0], obs["me"][1] + DELTAS[a][1])
        if not (obs["walls"][t] or t in bombs or t == obs["opp"]):
            moves.append(a)
    return [Action.STAY, Action.BOMB, *moves]
