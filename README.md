# BOMBcompeTItion

A two-player bomb game for the class bot competition. Each team writes one bot; bots play each other
in a league and are ranked by kills.

<p align="center"><img src="images/match.gif" width="400"></p>

## Setup

```bash
pip install -e .    # Python >= 3.10
```

## Rules

<p align="center"><img src="images/board.png" width="400"></p>

The board is a fixed 9x9 map. Cells are `(row, col)` with row 0 at the top. Player A starts at `(1, 1)`,
player B at `(7, 7)`. Grey blocks are walls.

Each step both players choose one action at the same time:

| 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| STAY | UP | DOWN | LEFT | RIGHT | BOMB |

A step is resolved in this order:

1. Bombs are dropped on the players' cells (at most 2 bombs per player on the board).
2. Players move. Walls, bombs and the other player's cell block a move. If both move into the same cell, neither moves.
3. Every bomb's fuse goes down by 1. A bomb at 0 explodes: its cell and up to 2 cells in each direction,
   stopped by walls. An explosion that reaches another bomb sets it off too.
4. A player in an explosion loses a life. Then both players go back to their start cells and all bombs are removed.

A bomb explodes 5 steps after the step it was dropped in. Each player has 3 lives. If the opponent's
bomb was part of the explosion that hit you, the opponent gets a kill; your own bomb gives no kill.
The game ends when someone has no lives left or after 300 steps.

The values are in `bombcompetition.RULES`.

## Your bot

A bot is a folder with a `policy.py`. Write yours in `submission/policy.py`:

```python
class Policy:
    def __init__(self):   # once per game
        ...

    def act(self, obs):   # every step, returns 0-5
        ...
```

If `act` raises an exception or returns something else, the bot stays for that step (a fault).
Time limits: TBD.

`obs` is a dict, the same board for both players:

| key | value |
|---|---|
| `player` | 0 if you are A, 1 if you are B |
| `walls` | numpy bool array `(9, 9)`, `walls[row, col]` |
| `me`, `opp` | `(row, col)` of you and the opponent |
| `bombs` | tuple of `{"pos": (row, col), "owner": 0 or 1, "fuse": steps until it explodes}` |
| `lives` | `(yours, opponent's)` |
| `step` | steps played so far (the game ends at 300) |

What you do with it is up to you. `legal_actions(obs)` returns the actions that are not blocked.
`examples/simple/policy.py` is a small example bot.

## Running games

```bash
python run_match.py --p1 submission --p2 examples/simple --games 20
```

`--p1` plays A and `--p2` plays B; any bot folder works for either. It prints wins, draws, losses,
kills, deaths and faults for each bot:

```
p1 submission: 0W 12D 8L  kills 0  deaths 36  faults 0  slowest act 0 ms
p2 examples/simple: 8W 12D 0L  kills 36  deaths 27  faults 0  slowest act 0 ms
```

Add `--replay replay.json` to also save one game. Open `web/replay.html` in a browser and load the
file to step through it; each step shows the actions both players chose.

For reinforcement learning, `bombcompetition.BomberEnv(opponent, player)` is a Gymnasium env where
you play one side and `opponent` (any `obs -> action` function) plays the other. The default reward
is +1 per kill and -1 per life lost; use `info["deaths"]` or `env.game` to build your own.

## Submission

Zip the contents of `submission/` (with `policy.py` at the top) as `<team>.zip` and upload it to TBD by TBD.
Only change files in `submission/`; the league uses its own copy of `bombcompetition/`.
Allowed libraries: TBD.

## Evaluation

Every pair of teams plays TBD games, swapping sides. Teams are ranked by total kills against other teams,
together with results against TA bots (TBD). The league is run with `league.py`.

Board sprites from [CoderOne Bomberland](https://github.com/CoderOneHQ/bomberland) (MIT).
