"""Example bot: turns the observation into a grid and a tensor, then moves to a random empty cell.
It shows how to read and process obs; it has no strategy."""

import numpy as np

from bombcompetition import DELTAS, Action

FLOOR, WALL, ME, OPP, BOMB = 0, 1, 2, 3, 4


def to_grid(obs):
    """2D map of the board: what is on each cell, and the fuse of each bomb."""
    grid = np.where(obs["walls"], WALL, FLOOR)
    fuse = np.zeros(grid.shape, dtype=int)
    for bomb in obs["bombs"]:  # {"pos": (row, col), "owner": 0 or 1, "fuse": steps until it explodes}
        grid[bomb["pos"]] = BOMB
        fuse[bomb["pos"]] = bomb["fuse"]
    grid[obs["me"]] = ME  # drawn last: you can stand on your own bomb
    grid[obs["opp"]] = OPP
    return grid, fuse


def to_tensor(obs):
    """The same board as float channels (e.g. as input for a neural network)."""
    grid, fuse = to_grid(obs)
    my_lives, opp_lives = obs["lives"]
    return np.stack([
        grid == WALL, grid == ME, grid == OPP, fuse,
        np.full(grid.shape, my_lives), np.full(grid.shape, opp_lives),
        np.full(grid.shape, obs["player"]),
    ]).astype(np.float32)


class Policy:
    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        grid, _ = to_grid(obs)
        r, c = obs["me"]
        moves = [a for a in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)
                 if grid[r + DELTAS[a][0], c + DELTAS[a][1]] == FLOOR]
        return int(self.rng.choice([Action.STAY, Action.BOMB, *moves]))


if __name__ == "__main__":
    from bombcompetition import Game

    game = Game()
    game.step(Action.BOMB, Action.UP)
    obs = game.obs(0)
    grid, fuse = to_grid(obs)
    print("grid (0 floor, 1 wall, 2 me, 3 opp, 4 bomb):\n", grid)
    print("tensor:", to_tensor(obs).shape)
    print("action:", Action(Policy().act(obs)).name)
