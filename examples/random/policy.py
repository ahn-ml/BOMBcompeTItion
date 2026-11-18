"""The simplest agent: read the observation, list the legal actions, pick one at random.

Run `python examples/random/policy.py` to see what an observation looks like.
"""

import numpy as np

# Actions (the only thing act() may return)
STAY, UP, DOWN, LEFT, RIGHT, BOMB = range(6)
MOVES = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}

FUSE = 6  # league rule: a bomb explodes FUSE steps after it is placed


def read_obs(obs):
    """Turn the (9, H, W) observation into plain Python values.

    Both players see the same board (no rotation). Positions are (row, col);
    row 0 is the top. "me"/"opp" are already sorted out for you, and "player"
    tells you which side you are: 0 = A (starts top-left), 1 = B (bottom-right).
    """
    return {
        "player": int(obs[8, 0, 0]),                           # 0 = A, 1 = B
        "walls": obs[0] > 0,                                   # bool (H, W), True = wall
        "me": tuple(int(x) for x in np.argwhere(obs[1])[0]),   # (row, col)
        "opp": tuple(int(x) for x in np.argwhere(obs[2])[0]),  # (row, col)
        # bombs: {(row, col): steps until it explodes}
        "my_bombs": {(int(r), int(c)): round(obs[3, r, c] * FUSE) for r, c in np.argwhere(obs[3] > 0)},
        "opp_bombs": {(int(r), int(c)): round(obs[4, r, c] * FUSE) for r, c in np.argwhere(obs[4] > 0)},
        "my_lives": float(obs[5, 0, 0]),       # fraction of starting lives (1.0 = all left)
        "opp_lives": float(obs[6, 0, 0]),
        "time_left": float(obs[7, 0, 0]),      # 1.0 at the start, 0.0 at the step limit
    }


def legal_actions(s):
    """Moves into walls, bombs or the opponent do nothing, so skip them."""
    blocked = set(s["my_bombs"]) | set(s["opp_bombs"]) | {s["opp"]}
    r, c = s["me"]
    actions = [STAY, BOMB]
    for a, (dr, dc) in MOVES.items():
        t = (r + dr, c + dc)
        if not s["walls"][t] and t not in blocked:
            actions.append(a)
    return actions


class Policy:
    def __init__(self):
        # Called once per game. Load model weights here if you have any.
        self.rng = np.random.default_rng()

    def act(self, obs):
        s = read_obs(obs)
        return int(self.rng.choice(legal_actions(s)))


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from bomber_env import Game

    g = Game()
    g.step(BOMB, STAY)  # player A drops a bomb
    print(g.render(), "\n")
    obs = g.obs(1)  # what player B sees
    print("obs shape:", obs.shape)
    for k, v in read_obs(obs).items():
        print(f"{k:>9}:", v if k != "walls" else f"{v.sum()} wall cells")
    print("legal actions:", legal_actions(read_obs(obs)))
    print("Policy().act(obs) ->", Policy().act(obs))
