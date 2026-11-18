"""Your bot. This folder is your submission: policy.py plus any files it loads
(e.g. weights via Path(__file__).parent / "weights.npz"). Policy() gets 10 s per game, act() 100 ms per step;
being too slow, raising, or returning something other than 0-5 means you STAY that step.
"""

from bombcompetition import RULES, Action, parse


class Policy:
    def __init__(self):
        pass

    def act(self, obs):
        view = parse(obs)
        # view.player: 0 = A (starts top-left), 1 = B (starts bottom-right)
        # view.me, view.opp: (row, col), row 0 is the top
        # view.walls: bool array; view.my_bombs / view.opp_bombs: {(row, col): steps until explosion}
        # view.my_lives, view.opp_lives, view.steps_left, view.legal_actions()
        # RULES: fuse, radius, max_bombs, lives, max_steps
        return Action.STAY
