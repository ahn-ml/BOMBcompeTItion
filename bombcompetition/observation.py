"""The observation a policy gets (built by Game.obs), and `parse` to read it back into plain values.

float32 array of shape (9, size, size). Both players see the same board (no rotation;
row 0 is the top). Channels:
  0 walls
  1 me                      2 opponent
  3 my bombs (fuse/FUSE)    4 opponent bombs (fuse/FUSE)
  5 my lives / LIVES        6 opponent lives / LIVES      (constant planes)
  7 steps left / MAX_STEPS  8 who I am: 0 = A, 1 = B      (constant planes)
"""

from dataclasses import dataclass

import numpy as np

from .game import Cell
from .rules import DELTAS, MOVES, RULES, Action, Rules


@dataclass
class View:
    """Everything in one observation, as plain Python values."""

    player: int                  # 0 = A, 1 = B
    walls: np.ndarray            # bool (size, size), True = wall
    me: Cell
    opp: Cell
    my_bombs: dict[Cell, int]    # bomb cell -> steps until it explodes
    opp_bombs: dict[Cell, int]
    my_lives: int
    opp_lives: int
    steps_left: int

    @property
    def bombs(self) -> dict[Cell, int]:
        return {**self.my_bombs, **self.opp_bombs}

    def can_move(self, action: Action) -> bool:
        """False if the move would hit a wall, a bomb or the opponent (you would just stay)."""
        dr, dc = DELTAS[action]
        t = (self.me[0] + dr, self.me[1] + dc)
        return t == self.me or not (self.walls[t] or t in self.bombs or t == self.opp)

    def legal_actions(self) -> list[Action]:
        """STAY, BOMB and every move that actually moves you."""
        return [Action.STAY, Action.BOMB] + [a for a in MOVES if self.can_move(a)]


def parse(obs: np.ndarray, rules: Rules = RULES) -> View:
    def cell(ch):
        r, c = np.argwhere(obs[ch])[0]
        return (int(r), int(c))

    def bombs(ch):
        return {(int(r), int(c)): round(float(obs[ch, r, c]) * rules.fuse) for r, c in np.argwhere(obs[ch] > 0)}

    return View(
        player=int(obs[8, 0, 0]),
        walls=obs[0] > 0,
        me=cell(1),
        opp=cell(2),
        my_bombs=bombs(3),
        opp_bombs=bombs(4),
        my_lives=round(float(obs[5, 0, 0]) * rules.lives),
        opp_lives=round(float(obs[6, 0, 0]) * rules.lives),
        steps_left=round(float(obs[7, 0, 0]) * rules.max_steps),
    )
