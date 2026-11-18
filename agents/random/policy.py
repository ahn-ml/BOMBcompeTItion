import numpy as np

from bombcompetition import parse


class Policy:
    """Picks a random action that is not blocked."""

    def __init__(self):
        self.rng = np.random.default_rng()

    def act(self, obs):
        return int(self.rng.choice(parse(obs).legal_actions()))
