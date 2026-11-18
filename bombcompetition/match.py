"""Load submitted policies and play games between them."""

import importlib.util
from collections.abc import Callable
from pathlib import Path

import numpy as np

from .game import Game
from .render import save_gif, to_rgb
from .rules import RULES, Rules

ActFn = Callable[[np.ndarray], int]


def load_policy(folder: str | Path) -> type:
    """Import <folder>/policy.py and return its Policy class."""
    path = Path(folder).resolve() / "policy.py"
    spec = importlib.util.spec_from_file_location(f"policy_{path.parent.name}_{id(path)}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Policy


def play_match(act0: ActFn, act1: ActFn, rules: Rules = RULES, gif: str | Path | None = None) -> Game:
    """Play one game (act0 is A, act1 is B) and return the finished Game.
    With `gif`, also save the game as an animated GIF."""
    game = Game(rules)
    frames = [to_rgb(game)] if gif else None
    while not game.done:
        game.step(act0(game.obs(0)), act1(game.obs(1)))
        if gif:
            frames.append(to_rgb(game))
    if gif:
        save_gif(frames, gif)
    return game
