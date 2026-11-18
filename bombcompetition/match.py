"""Loading bots and playing games between them."""

import importlib.util
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .game import RULES, Action, Game, Rules
from .render import save_gif, to_rgb

def load_policy(folder: str | Path) -> type:
    """The Policy class from <folder>/policy.py."""
    path = Path(folder).resolve() / "policy.py"
    spec = importlib.util.spec_from_file_location(f"policy_{abs(hash(path))}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Policy


def play_match(act0: Callable[[np.ndarray], int], act1: Callable[[np.ndarray], int],
               rules: Rules = RULES, gif: str | Path | None = None) -> Game:
    """Play one game, act0 as A and act1 as B, and return the finished game (optionally saved as a GIF)."""
    game = Game(rules)
    frames = [to_rgb(game)] if gif else []
    while not game.done:
        game.step(act0(game.obs(0)), act1(game.obs(1)))
        if gif:
            frames.append(to_rgb(game))
    if gif:
        save_gif(frames, gif)
    return game


class SafeBot:
    """Runs a submitted Policy so that it cannot crash a game: an exception or an invalid
    action makes the bot STAY for that step and counts as a fault.
    No time limit is enforced yet; `slowest` records the slowest act() call."""

    def __init__(self, policy_cls: type):
        self.faults, self.errors, self.slowest = 0, [], 0.0
        _, self.policy = self._call(policy_cls)

    def _fault(self, message: str):
        self.faults += 1
        if len(self.errors) < 5:
            self.errors.append(message)

    def _call(self, fn, *args):
        try:
            return True, fn(*args)
        except Exception as e:
            self._fault(f"{getattr(fn, '__qualname__', fn)}: {e!r}")
            return False, None

    def act(self, obs) -> int:
        if self.policy is None:
            return Action.STAY
        start = time.perf_counter()
        ok, action = self._call(self.policy.act, obs)
        self.slowest = max(self.slowest, time.perf_counter() - start)
        if ok and isinstance(action, (int, np.integer)) and 0 <= action <= 5:
            return int(action)
        if ok:
            self._fault(f"act returned {action!r}, expected an int 0-5")
        return Action.STAY


@dataclass
class Record:
    kills: int = 0
    deaths: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    faults: int = 0
    slowest: float = 0.0  # seconds, slowest act()
    errors: list[str] = field(default_factory=list)


def play_series(bot_a: type, bot_b: type, games: int, rules: Rules = RULES, swap: bool = True) -> tuple[Record, Record]:
    """Play `games` games between two Policy classes. bot_a plays A, bot_b plays B;
    with `swap`, they change sides every other game."""
    records = (Record(), Record())
    for i in range(games):
        order = (1, 0) if swap and i % 2 else (0, 1)  # order[side] = which bot plays that side
        bots = [SafeBot((bot_a, bot_b)[order[side]]) for side in (0, 1)]
        game = Game(rules)
        while not game.done:
            game.step(bots[0].act(game.obs(0)), bots[1].act(game.obs(1)))
        winner = game.winner()
        for side, bot in enumerate(bots):
            r = records[order[side]]
            r.kills += game.kills[side]
            r.deaths += rules.lives - game.lives[side]
            r.wins += winner == side
            r.draws += winner is None
            r.losses += winner == 1 - side
            r.faults += bot.faults
            r.slowest = max(r.slowest, bot.slowest)
            r.errors += bot.errors[: 5 - len(r.errors)]
    return records
