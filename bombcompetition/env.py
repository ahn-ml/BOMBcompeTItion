"""Gymnasium env: you play one side, `opponent` (obs -> action) plays the other."""

import gymnasium as gym
import numpy as np

from .game import RULES, Game, Rules
from .render import to_rgb, to_text


class BomberEnv(gym.Env):
    """Default reward: +1 when your bomb kills the opponent, -1 when you lose a life.
    Build your own from `info["deaths"]` or `env.game` (e.g. with a gymnasium.Wrapper)."""

    metadata = {"render_modes": ["ansi", "rgb_array"], "render_fps": 4}

    def __init__(self, opponent, player: int = 0, rules: Rules = RULES, render_mode: str | None = None):
        self.opponent, self.player, self.rules, self.render_mode = opponent, player, rules, render_mode
        size = Game(rules).size
        self.observation_space = gym.spaces.Box(0.0, 1.0, (9, size, size), np.float32)
        self.action_space = gym.spaces.Discrete(6)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.game = Game(self.rules)
        return self.game.obs(self.player), {}

    def step(self, action):
        game, me = self.game, self.player
        actions = [0, 0]
        actions[me], actions[1 - me] = int(action), int(self.opponent(game.obs(1 - me)))
        deaths = game.step(*actions)
        reward = sum((d.killer == me) - (d.player == me) for d in deaths)
        terminated = min(game.lives) <= 0
        info = {"deaths": deaths, "lives": tuple(game.lives), "kills": tuple(game.kills)}
        return game.obs(me), float(reward), terminated, game.done and not terminated, info

    def render(self):
        return to_rgb(self.game) if self.render_mode == "rgb_array" else to_text(self.game)
