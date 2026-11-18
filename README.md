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

Start from `agents/my_team` and test against the examples:

```bash
cp -r agents/my_team agents/<team>
python run_match.py agents/<team> agents/simple --games 20
python run_match.py agents/<team> agents/simple --gif match.gif
```

`run_match.py` uses the league's limits: a slow step, an exception or an invalid action is reported
as a fault (and counts as STAY). Submit the folder once it plays without faults.

## Observation

`float32 (9, 9, 9)`, the same board for both players, row 0 at the top:

| Channel | |
|---|---|
| 0 | walls |
| 1, 2 | me, opponent |
| 3, 4 | my bombs, opponent bombs (steps until explosion / 6) |
| 5, 6 | my lives, opponent lives (/ 3) |
| 7 | steps left (/ 300) |
| 8 | 0 if I am A (start top-left), 1 if I am B (start bottom-right) |

What you do with it is up to you. Some helpers:

- `parse(obs)` → `View` with `me`, `opp`, `my_bombs`, `opp_bombs`, lives, `legal_actions()`
- `blast_cells(walls, cell, radius)` → cells a bomb at `cell` hits
- `to_game(obs)` → a `Game` you can `step(a0, a1)` to simulate ahead
- `BomberEnv(opponent, player)` → gymnasium env for RL. The default reward is +1 per kill and
  -1 per life lost; `info["deaths"]` and `env.game` let you build your own. The opponent can be
  any `obs -> action`, including your own bot.

## Evaluation

Every pair of teams plays several games, swapping sides. Ranking: total kills, plus results
against TA bots. See `league.py`.

## Layout

```
bombcompetition/   game.py (rules, Game), view.py (parse, to_game), env.py, render.py, match.py
agents/            my_team (template), random, simple
run_match.py       play two bots
league.py          the league
web/               browser version (python tools/build_web.py rebuilds play.html)
tests/             rule tests
tools/             sprite and web build scripts
```

Board sprites: [CoderOne Bomberland](https://github.com/CoderOneHQ/bomberland) (MIT, `bombcompetition/assets/LICENSE-bomberland.md`).
