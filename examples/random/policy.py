"""The simplest bot: read the observation, pick a random legal action.

Run `python examples/random/policy.py` to see what an observation contains.
"""

import numpy as np

from bombcompetition import parse


class Policy:
    def __init__(self):
        # Called once per game. Load model weights here if you have any.
        self.rng = np.random.default_rng()

    def act(self, obs: np.ndarray) -> int:
        view = parse(obs)  # positions, bombs, lives, ... (see bombcompetition/observation.py)
        return int(self.rng.choice(view.legal_actions()))


if __name__ == "__main__":
    from bombcompetition import Action, Game
    from bombcompetition.render import to_text

    game = Game()
    game.step(Action.BOMB, Action.STAY)  # A drops a bomb
    print(to_text(game), "\n")

    obs = game.obs(1)  # what B sees
    print("obs:", obs.shape, obs.dtype)
    view = parse(obs)
    for name, value in vars(view).items():
        print(f"{name:>10}:", f"{int(value.sum())} wall cells" if name == "walls" else value)
    print("legal actions:", [a.name for a in view.legal_actions()])
