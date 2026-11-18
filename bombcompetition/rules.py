"""Game constants and the rule set. `RULES` is the official league rule set."""

from dataclasses import dataclass
from enum import IntEnum

MAPS = {
    "rooms": (
        "#########",
        "#A..#...#",
        "#.#.#.#.#",
        "#.#...#.#",
        "#...#...#",
        "#.#...#.#",
        "#.#.#.#.#",
        "#...#..B#",
        "#########",
    ),
    "pillar": (
        "#########",
        "#A......#",
        "#.#.#.#.#",
        "#.......#",
        "#.#.#.#.#",
        "#.......#",
        "#.#.#.#.#",
        "#......B#",
        "#########",
    ),
}


class Action(IntEnum):
    STAY = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    BOMB = 5


# (d_row, d_col) of each action; row 0 is the top of the board
DELTAS = {
    Action.STAY: (0, 0),
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
    Action.BOMB: (0, 0),
}
MOVES = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)


@dataclass(frozen=True)
class Rules:
    """
    layout:    a name in MAPS, or rows of a square map ('#' wall, '.' floor, 'A'/'B' start cells).
               The border must be all walls.
    starts:    ((row, col), (row, col)) start cells of A and B; None = the 'A'/'B' cells in the layout.
    fuse:      steps from placing a bomb until it explodes.
    radius:    how many cells an explosion reaches in each of the 4 directions.
    max_bombs: bombs one player may have on the board at once.
    lives:     lives per player.
    max_steps: the game stops after this many steps.
    """

    layout: str | tuple[str, ...] = "rooms"
    starts: tuple[tuple[int, int], tuple[int, int]] | None = None
    fuse: int = 6
    radius: int = 2
    max_bombs: int = 2
    lives: int = 3
    max_steps: int = 300

    @property
    def rows(self):
        return MAPS[self.layout] if isinstance(self.layout, str) else tuple(self.layout)


RULES = Rules()
