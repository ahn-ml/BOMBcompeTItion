# BOMBcompeTItion

A 1v1 bomb game on a fixed 9x9 map. Each team writes one bot; bots play each other in a league.

```bash
pip install -e .
```

Open `web/play.html` in a browser to play the game yourself.

## Rules

Each step both players pick an action at the same time:
`0 STAY, 1 UP, 2 DOWN, 3 LEFT, 4 RIGHT, 5 BOMB`.

- A bomb is dropped on your cell; you can have 2 on the board at once.
- Walls, bombs and the other player block moves. Two players moving into the same cell both stay.
- A bomb explodes 6 steps after it is dropped, 2 cells in each direction. Walls stop it; bombs it reaches explode too.
- A player in an explosion loses a life (3 in total), and both players restart from their start cells with no bombs.
  If the opponent's bomb hit you, the opponent gets a **kill**. Your own bomb hurts you but gives no kill.
- The game ends when someone runs out of lives or after 300 steps.

All values are in `bombcompetition.RULES` (`bombcompetition/game.py`).

## Your bot

A bot is a folder with a `policy.py`:

```python
class Policy:
    def __init__(self): ...      # once per game, 10 s limit
    def act(self, obs): ...      # every step, 100 ms limit, returns 0-5
```

Write it in `submission/policy.py` and test it against the examples:

```bash
python run_match.py submission examples/random --games 20
python run_match.py submission examples/random --gif replay.gif
```

`run_match.py` uses the league's limits: a slow step, an exception or an invalid action is reported
as a fault (and counts as STAY). Once it plays without faults, zip the `submission/` folder
(with `policy.py` at the top) as `<team>.zip` and hand it in.

## Observation

`obs` is the game state as it is, a dict (the same board for both players, row 0 at the top):

```python
{
    "player": 0,                       # 0 = A (starts top-left), 1 = B (starts bottom-right)
    "walls": walls,                    # bool array (9, 9); walls[row, col]
    "me": (2, 1), "opp": (6, 7),       # (row, col)
    "bombs": ({"pos": (1, 1), "owner": 0, "fuse": 4},   # fuse = steps until it explodes
              {"pos": (6, 7), "owner": 1, "fuse": 5}),
    "lives": (3, 3),                   # (mine, opponent's)
    "step": 2,                         # steps played so far
}
```

Turning it into features, tensors or anything else is up to you. `legal_actions(obs)` lists the
actions that are not blocked.

For reinforcement learning there is a gymnasium env, `BomberEnv(opponent, player)`, with the same dict
observations. Its default reward is +1 per kill and -1 per life lost; `info["deaths"]` and `env.game`
let you build your own. The opponent can be any `obs -> action`, including your own bot.

## Evaluation

Every pair of teams plays several games, swapping sides. Ranking: total kills, plus results
against TA bots. See `league.py`.

## Layout

```
bombcompetition/   game.py (rules, Game, observations), env.py, render.py, match.py
submission/        your bot (what you hand in)
examples/random/   example bot: obs → grid / tensor, then a random move (no strategy)
run_match.py       play two bots
league.py          the league
web/               browser version (python tools/build_web.py rebuilds play.html)
tests/             rule tests
tools/             sprite and web build scripts
```

Board sprites: [CoderOne Bomberland](https://github.com/CoderOneHQ/bomberland) (MIT, `bombcompetition/assets/LICENSE-bomberland.md`).
