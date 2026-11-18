"""Reading observations.

An observation is float32 (9, size, size), the same board for both players:
  0 walls       1 me          2 opponent
  3 my bombs    4 opp bombs   (steps until explosion / fuse)
  5 my lives    6 opp lives   (/ lives)
  7 steps left (/ max_steps)  8 who I am: 0 = A, 1 = B
"""

from dataclasses import dataclass

import numpy as np

from .game import DELTAS, MOVES, RULES, Action, Bomb, Cell, Game, Rules


@dataclass
class View:
    player: int
    walls: np.ndarray  # bool, True = wall
    me: Cell
    opp: Cell
    my_bombs: dict[Cell, int]  # cell -> steps until it explodes
    opp_bombs: dict[Cell, int]
    my_lives: int
    opp_lives: int
    steps_left: int

    @property
    def bombs(self) -> dict[Cell, int]:
        return self.my_bombs | self.opp_bombs

    def legal_actions(self) -> list[Action]:
        """STAY, BOMB and the moves that are not blocked."""
        moves = []
        for a in MOVES:
            t = (self.me[0] + DELTAS[a][0], self.me[1] + DELTAS[a][1])
            if not (self.walls[t] or t in self.bombs or t == self.opp):
                moves.append(a)
        return [Action.STAY, Action.BOMB, *moves]


def parse(obs: np.ndarray, rules: Rules = RULES) -> View:
    def cell(ch):
        return tuple(int(x) for x in np.argwhere(obs[ch])[0])

    def bombs(ch):
        return {(int(r), int(c)): round(obs[ch, r, c] * rules.fuse) for r, c in np.argwhere(obs[ch])}

    return View(
        player=int(obs[8, 0, 0]),
        walls=obs[0] > 0,
        me=cell(1),
        opp=cell(2),
        my_bombs=bombs(3),
        opp_bombs=bombs(4),
        my_lives=round(obs[5, 0, 0] * rules.lives),
        opp_lives=round(obs[6, 0, 0] * rules.lives),
        steps_left=round(obs[7, 0, 0] * rules.max_steps),
    )


def to_game(obs: np.ndarray, rules: Rules = RULES) -> Game:
    """Rebuild the game from an observation, to simulate with `game.step`. Kill counts start at 0."""
    v = parse(obs, rules)
    me, opp = v.player, 1 - v.player
    game = Game(rules)
    game.pos[me], game.pos[opp] = v.me, v.opp
    game.lives[me], game.lives[opp] = v.my_lives, v.opp_lives
    game.t = rules.max_steps - v.steps_left
    game.bombs = {c: Bomb(me, f) for c, f in v.my_bombs.items()} | {c: Bomb(opp, f) for c, f in v.opp_bombs.items()}
    return game
