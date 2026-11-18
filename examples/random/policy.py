"""Example bot: how to read the observation and return an action. It plays randomly."""

import numpy as np

from bombcompetition import Action, legal_actions


class Policy:
    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        player = obs["player"]  # 0 = A, 1 = B
        me, opp = obs["me"], obs["opp"]  # (row, col)
        walls = obs["walls"]  # walls[row, col] is True for a wall
        for bomb in obs["bombs"]:
            pos, owner, fuse = bomb["pos"], bomb["owner"], bomb["fuse"]  # fuse: steps until it explodes
        my_lives, opp_lives = obs["lives"]
        step = obs["step"]

        actions = legal_actions(obs)  # STAY, BOMB and the moves that are not blocked
        return int(self.rng.choice(actions))  # one of Action.STAY, UP, DOWN, LEFT, RIGHT, BOMB (0-5)
