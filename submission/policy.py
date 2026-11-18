"""Your bot. This folder is your submission: policy.py plus any files it loads
(e.g. weights via Path(__file__).parent / "weights.npz"). Policy() gets 10 s per game,
act() 100 ms per step; being too slow, raising, or returning something other than 0-5
means you STAY that step.
"""

from bombcompetition import RULES, Action


class Policy:
    def __init__(self):
        pass

    def act(self, obs):
        # obs["player"]  0 = A (starts top-left), 1 = B (starts bottom-right)
        # obs["walls"]   bool array, obs["walls"][row, col]; row 0 is the top
        # obs["me"], obs["opp"]  (row, col)
        # obs["bombs"]   [{"pos": (row, col), "owner": 0 or 1, "fuse": steps until it explodes}, ...]
        # obs["lives"]   (mine, opponent's)
        # obs["step"]    steps played so far (the game ends at RULES.max_steps)
        # RULES: fuse, radius, max_bombs, lives, max_steps
        return Action.STAY
