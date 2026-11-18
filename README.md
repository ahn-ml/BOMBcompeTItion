# BOMBcompeTItion

A tiny 1v1 Bomberman-style environment for an RL lab: Nubzuki (A) vs the KAIST goose (B)
on a fixed 9x9 map with bombs and fixed walls only. Based on the rules of
[CoderOne Bomberland](https://github.com/CoderOneHQ/bomberland), heavily simplified.

## Install

```bash
pip install -r requirements.txt   # numpy, gymnasium, pillow
python bomber_env.py              # self-check, prints "ok"
```

## Try it

- Play in the browser: open `web/play.html` (human vs bot, 2 players on one keyboard, or bot vs bot).
- See what an observation looks like: `python examples/random/policy.py`
- Bot vs bot: `python run_match.py examples/greedy examples/simple --games 20`
- Save a replay: `python run_match.py examples/greedy examples/simple --gif match.gif`

## Rules (defaults)

One step = both players act at the same time. Actions: `0 stay, 1 up, 2 down, 3 left, 4 right, 5 bomb`.

1. Bomb: placed on your own cell, at most `max_bombs=2` of yours at once.
2. Move: blocked by walls, bombs and the other player. Both moving into the same cell: nobody moves.
3. Bombs explode `fuse=6` steps after placement, in a cross of `radius=2`, stopped by walls, chaining other bombs.
4. A player in an explosion loses a life (`lives=3`), then both go back to their start cells and bombs are cleared.
5. A kill counts only when your bomb hits the opponent (suicides are not kills).
6. Game over when someone has no lives or after `max_steps=300`.

All of these, the map (`layout`) and the start cells (`starts`) are keyword arguments of
`Game`, `BomberEnv`, `play_match` and `save_gif`. See the docstring of `bomber_env.py`.

## Gymnasium env

```python
from bomber_env import BomberEnv

env = BomberEnv(opponent=lambda obs: 0, player=0)  # opponent: obs -> action
obs, info = env.reset(seed=0)                      # obs: float32 (9, 9, 9)
obs, reward, terminated, truncated, info = env.step(5)
```

Observation channels: `0 walls, 1 me, 2 opponent, 3 my bombs (fuse/FUSE), 4 opponent bombs,
5 my lives, 6 opponent lives, 7 steps left, 8 which player I am (0 = A, 1 = B)`.
Both players see the same board coordinates (no rotation).
Reward: +1 for a kill by your bomb, -1 when you lose a life.

## Submission (draft)

A folder with `policy.py` defining:

```python
class Policy:
    def __init__(self): ...                  # once per game; load weights relative to __file__
    def act(self, obs) -> int: ...           # 0..5, within 100 ms
```

Timeouts, exceptions and invalid actions count as "stay".

## League (TA)

```bash
python league.py --teams submissions --ta ta_bots --games 10
```

Every pair of teams plays, and every team plays every TA bot. Ranking is planned as total kills
plus results against the TA bots. Results go to `league_results.csv`.

## Files

| Path | What |
|---|---|
| `bomber_env.py` | game rules, gymnasium env, rendering |
| `examples/random`, `examples/simple`, `examples/greedy` | example bots (weak → strong) |
| `run_match.py` | play two bots, optionally save a GIF |
| `league.py` | round-robin league with timeouts |
| `web/play.html` | playable browser version (same rules, generated from the same sprites) |
| `assets/` | sprites: tiles/bombs from Bomberland (MIT, see `assets/LICENSE-bomberland.md`), mascots drawn by `assets/draw_mascots.py` |
