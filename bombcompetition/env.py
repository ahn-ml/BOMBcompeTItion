"""Gymnasium wrapper: you control one player, a fixed opponent policy controls the other."""

from collections.abc import Callable

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .game import N_CHANNELS, Game
from .rules import RULES, Rules
from .render import to_rgb, to_text


class BomberEnv(gym.Env):
    """
    opponent: obs -> action for the other player (e.g. `Policy().act` of an example bot).
    player:   which side you play, 0 = A or 1 = B.

    Reward per step: +1 when your bomb kills the opponent, -1 when you lose a life
    (to any bomb, including your own). `terminated` when someone is out of lives,
    `truncated` at the step limit.
    """

    metadata = {"render_modes": ["ansi", "rgb_array"], "render_fps": 4}

    def __init__(self, opponent: Callable[[np.ndarray], int], player: int = 0,
                 rules: Rules = RULES, render_mode: str | None = None):
        self.opponent = opponent
        self.player = player
        self.rules = rules
        self.render_mode = render_mode
        size = Game(rules).size  # also validates the rules
        self.observation_space = spaces.Box(0.0, 1.0, (N_CHANNELS, size, size), np.float32)
        self.action_space = spaces.Discrete(6)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.game = Game(self.rules)
        return self.game.obs(self.player), {}

    def step(self, action):
        g, me, opp = self.game, self.player, 1 - self.player
        actions = [0, 0]
        actions[me] = int(action)
        actions[opp] = int(self.opponent(g.obs(opp)))
        deaths = g.step(*actions)
        reward = sum((d.killer == me) - (d.player == me) for d in deaths)
        terminated = min(g.lives) <= 0
        truncated = g.done and not terminated
        info = {"lives": tuple(g.lives), "kills": tuple(g.kills)}
        return g.obs(me), float(reward), terminated, truncated, info

    def render(self):
        return to_rgb(self.game) if self.render_mode == "rgb_array" else to_text(self.game)
