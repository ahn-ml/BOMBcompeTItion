"""Gymnasium env: you play one side, `opponent` (obs -> action) plays the other."""

import gymnasium as gym

from .game import RULES, Game, Rules
from .render import to_rgb, to_text


class BomberEnv(gym.Env):
    """Default reward: +1 when your bomb kills the opponent, -1 when you lose a life.
    Build your own from `info["deaths"]` or `env.game` (e.g. with a gymnasium.Wrapper)."""

    metadata = {"render_modes": ["ansi", "rgb_array"], "render_fps": 4}

    def __init__(self, opponent, player: int = 0, rules: Rules = RULES, render_mode: str | None = None):
        self.opponent, self.player, self.rules, self.render_mode = opponent, player, rules, render_mode
        n, sp = Game(rules).size, gym.spaces
        cell = sp.Tuple((sp.Discrete(n), sp.Discrete(n)))
        bomb = sp.Dict({"pos": cell, "owner": sp.Discrete(2), "fuse": sp.Discrete(rules.fuse + 1)})
        self.observation_space = sp.Dict({
            "player": sp.Discrete(2),
            "walls": sp.MultiBinary((n, n)),
            "me": cell,
            "opp": cell,
            "bombs": sp.Sequence(bomb),
            "lives": sp.Tuple((sp.Discrete(rules.lives + 1),) * 2),
            "step": sp.Discrete(rules.max_steps + 1),
        })
        self.action_space = sp.Discrete(6)

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
