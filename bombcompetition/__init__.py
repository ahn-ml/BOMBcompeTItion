"""BOMBcompeTItion: a 1v1 bomb game (Nubzuki vs the KAIST goose) for an RL lab."""

from .env import BomberEnv
from .game import N_CHANNELS, Death, Game, blast_cells
from .match import load_policy, play_match
from .observation import View, parse
from .rules import DELTAS, MAPS, MOVES, RULES, Action, Rules

__all__ = [
    "Action", "BomberEnv", "DELTAS", "Death", "Game", "MAPS", "MOVES", "N_CHANNELS", "RULES", "Rules", "View",
    "blast_cells", "load_policy", "parse", "play_match",
]
