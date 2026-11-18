# BOMBcompeTItion

A 1v1 bomb game for an RL lab: Nubzuki (A) vs the KAIST goose (B) on a fixed 9x9 map with
bombs and fixed walls only.

## Install

```bash
pip install -e ".[dev]"    # numpy, gymnasium, pillow (+ pytest)
python -m pytest tests     # rule tests
```

## Try it

| What | How |
|---|---|
| Play in the browser | open `web/play.html` (human vs bot, two players on one keyboard, or bot vs bot) |
| See an observation | `python examples/random/policy.py` |
| Bot vs bot | `python run_match.py examples/greedy examples/simple --games 20` |
| Save a replay | `python run_match.py examples/greedy examples/simple --gif match.gif` |

## Rules

One step = both players act at the same time. Actions: `STAY, UP, DOWN, LEFT, RIGHT, BOMB` (0-5).

1. A bomb is placed on your own cell; at most `max_bombs` of yours at once.
2. Moves are blocked by walls, bombs and the other player. If both move into the same cell, nobody moves.
3. A bomb explodes `fuse` steps after placement, in a cross of `radius` cells, stopped by walls,
   and sets off other bombs it reaches.
4. A player in an explosion loses a life; both players return to their start cells and bombs are cleared.
   It counts as a **kill** only if the opponent's bomb was part of that explosion (suicides are not kills).
5. The game ends when someone has no lives left or after `max_steps`.

The official values live in one place, `bombcompetition.RULES`:

```python
Rules(layout="rooms", starts=None, fuse=6, radius=2, max_bombs=2, lives=3, max_steps=300)
```

Use your own map, start cells or bomb rules with e.g.
`Rules(layout=("#####", "#A..#", "#...#", "#..B#", "#####"), fuse=4)` and pass it to
`Game`, `BomberEnv` or `play_match`.

## Observation

`float32 (9, 9, 9)`, the same board coordinates for both players (row 0 is the top):

| Channel | Content |
|---|---|
| 0 | walls |
| 1, 2 | me, opponent |
| 3, 4 | my bombs, opponent bombs (fuse / FUSE) |
| 5, 6 | my lives, opponent lives (/ LIVES) |
| 7 | steps left (/ MAX_STEPS) |
| 8 | who I am: 0 = A (top-left start), 1 = B (bottom-right start) |

`bombcompetition.parse(obs)` turns it into a `View` with plain values
(`me`, `opp`, `my_bombs`, `opp_bombs`, lives, `legal_actions()`, ...).

## Gymnasium env

```python
from bombcompetition import BomberEnv, load_policy

opponent = load_policy("examples/simple")()
env = BomberEnv(opponent=opponent.act, player=0)
obs, info = env.reset(seed=0)
obs, reward, terminated, truncated, info = env.step(5)
```

Reward: +1 when your bomb kills the opponent, -1 when you lose a life.

## Submission (draft)

A folder with `policy.py`:

```python
class Policy:
    def __init__(self): ...           # once per game; load weights relative to __file__
    def act(self, obs) -> int: ...    # 0..5, within 100 ms
```

Timeouts, exceptions and invalid actions count as `STAY`.

## League (TA)

```bash
python league.py --teams submissions --ta ta_bots --games 10
```

Every pair of teams plays, and every team plays every TA bot (sides swapped each game).
Planned ranking: total kills against other teams, plus results against the TA bots.
Results are printed and saved to `league_results.csv`.

## Layout

| Path | What |
|---|---|
| `bombcompetition/rules.py` | actions, maps, `Rules` / `RULES` |
| `bombcompetition/game.py` | the game (`Game`) and observations |
| `bombcompetition/observation.py` | `parse(obs)` → `View` for writing bots |
| `bombcompetition/env.py` | gymnasium env |
| `bombcompetition/render.py` | text / image rendering |
| `bombcompetition/match.py` | `load_policy`, `play_match` (optionally to GIF) |
| `examples/` | `random`, `simple` (student examples), `greedy` (TA reference) |
| `run_match.py`, `league.py` | match and league runners |
| `tests/` | rule tests, including 40 recorded games that must replay identically |
| `web/` | browser version: edit `template.html`, then `python tools/build_web.py` |
| `tools/draw_mascots.py` | pixel art of the two characters |

Board tiles, bombs and the explosion sprite come from
[CoderOne Bomberland](https://github.com/CoderOneHQ/bomberland) (MIT, see
`bombcompetition/assets/LICENSE-bomberland.md`).
