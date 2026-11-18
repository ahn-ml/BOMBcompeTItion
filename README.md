# BOMBcompeTItion

Write a bot for a two-player bomb game and enter it in the class league.

Two players start in opposite corners of a fixed 9x9 map. Every step both choose an action at the
same time: move, wait, or drop a bomb. Bombs explode a few steps later in a cross, and a player caught
in an explosion loses a life. Your bot scores a **kill** each time one of its bombs hits the opponent.
Each team submits one bot; bots play every other team's bot, and the ranking is based on kills.

<p align="center"><img src="images/match.gif" width="420" alt="Two example bots playing"></p>

- [1. Quick start](#1-quick-start)
- [2. Game rules](#2-game-rules)
- [3. Writing your bot](#3-writing-your-bot)
- [4. Testing locally](#4-testing-locally)
- [5. What you may and may not do](#5-what-you-may-and-may-not-do)
- [6. Submission](#6-submission)
- [7. Evaluation](#7-evaluation)
- [8. Checklist before you submit](#8-checklist-before-you-submit)
- [9. Optional: reinforcement learning](#9-optional-reinforcement-learning)

## 1. Quick start

```bash
git clone <this repository>
cd BOMBcompeTItion
pip install -e .        # Python >= 3.10; installs numpy, gymnasium, pillow
```

1. **Play the game yourself**: open `web/play.html` in a browser. Move with WASD or the arrow keys, drop
   a bomb with Space. Playing a few rounds is the fastest way to understand the rules.
2. **Read the example bot**: `examples/simple/policy.py`. It is short and shows how to read the
   observation and return an action. It plays badly on purpose.
3. **Write your bot** in `submission/policy.py`.
4. **Test it** against the example bot:

```bash
python run_match.py --p1 submission --p2 examples/simple --games 20
```

## 2. Game rules

### The board

<p align="center"><img src="images/board.png" width="420" alt="The board with row and column numbers"></p>

- The board is 9x9. Cells are written as `(row, col)`: row 0 is the top, col 0 is the left.
- The grey blocks are **walls**. They never change, cannot be walked through, and stop explosions.
  The outer border is all walls, so you can never leave the board.
- Player **A** starts at `(1, 1)` (top-left), player **B** at `(7, 7)` (bottom-right).
  The map is the same when rotated by 180 degrees, so neither side has an advantage.
- In the picture: A is at `(3, 3)`, B at `(5, 5)`. The number next to a bomb is how many steps are left
  until it explodes (A's bomb at `(1, 3)` has 4, B's bomb at `(7, 5)` has 2). The fire shows the cells
  hit by a bomb that exploded at `(5, 1)` in this step.

### Actions

Every step your bot returns one integer:

| Value | Action | Effect |
|---|---|---|
| 0 | `STAY` | do nothing |
| 1 | `UP` | move to `(row - 1, col)` |
| 2 | `DOWN` | move to `(row + 1, col)` |
| 3 | `LEFT` | move to `(row, col - 1)` |
| 4 | `RIGHT` | move to `(row, col + 1)` |
| 5 | `BOMB` | drop a bomb on the cell you are standing on |

`from bombcompetition import Action` gives these names (`Action.UP`, ...). A move or a bomb that is
not possible simply does nothing (you stay where you are).

### What happens in one step

Both players' actions are applied together, in this order:

1. **Bombs are dropped.** A player who chose `BOMB` drops a bomb on its own cell, unless there is
   already a bomb on that cell or the player already has **2** bombs on the board.
2. **Players move.** A move fails (the player stays) if the target cell is a wall, has a bomb, or is
   the cell the other player is standing on at the start of the step. If both players try to move into
   the same cell, neither moves. You may stand on a bomb you just dropped, but once you leave a bomb's
   cell you cannot step back onto it.
3. **Fuses go down by 1** for every bomb. A bomb whose fuse reaches 0 **explodes**.
4. **Explosions.** An explosion covers the bomb's cell and up to **2** cells in each of the four
   directions. A wall stops it in that direction (the wall cell itself is not hit). If an explosion
   reaches another bomb, that bomb explodes in the same step too (a chain), and the explosion goes on
   past it.
5. **Hits.** A player standing on any exploded cell loses a life. Both players can be hit in the same step.
6. **New round.** If anyone lost a life (and the game is not over), both players go back to their
   start cells and all bombs are removed.

### Bomb timing

A new bomb has a fuse of **6**, and the fuse already goes down in the step the bomb is dropped. So right
after you drop a bomb, the observation shows it with **5** steps left, and you get **5 more moves**
before it explodes at the end of the 5th step. In general, a bomb showing `fuse = f` explodes at the
end of the `f`-th step from now.

### Lives, kills and the end of a game

- Each player has **3 lives**.
- When a player loses a life to an explosion that includes a bomb of the **opponent**, the opponent
  gets a **kill**. Losing a life only to your own bombs gives nobody a kill (but you still lose the life).
- The game ends when a player has no lives left, or after **300 steps**.
- The player with more lives left wins the game; equal lives is a draw.
  The league ranking itself is based on kills (see [Evaluation](#7-evaluation)).

All of these numbers are in `bombcompetition.RULES`:

```python
Rules(fuse=6, radius=2, max_bombs=2, lives=3, max_steps=300, layout=MAP)
```

## 3. Writing your bot

### The interface

Your bot is the folder `submission/`. It must contain a `policy.py` with a class `Policy`:

```python
class Policy:
    def __init__(self):
        ...                 # called once at the start of every game

    def act(self, obs):
        ...                 # called every step; return an int from 0 to 5
```

- A new `Policy()` is created for **every game**, so you can keep information between steps of a game
  in `self` (for example, what the opponent did last step).
- Time limits for `__init__` and `act`: **TBD**. Keep `act` fast; `run_match.py` reports your slowest call.
- If `act` raises an exception or returns something other than an int from 0 to 5,
  your bot does `STAY` for that step and it counts as a **fault**. The game goes on.
- To load files from your folder (e.g. model weights), use paths relative to `policy.py`:
  `Path(__file__).parent / "weights.npz"`.

### The observation

`obs` is a Python dict describing the game exactly as it is. Both players see the same board in the
same coordinates; `obs["player"]` tells you which side you are.

```python
{
    "player": 0,                         # 0 if you are A, 1 if you are B
    "walls":  walls,                     # numpy bool array, shape (9, 9)
    "me":     (2, 1),                    # your (row, col)
    "opp":    (6, 7),                    # the opponent's (row, col)
    "bombs":  ({"pos": (1, 1), "owner": 0, "fuse": 4},
               {"pos": (6, 7), "owner": 1, "fuse": 5}),
    "lives":  (3, 2),                    # (your lives, the opponent's lives)
    "step":   12,                        # steps played so far, from 0 up to 300
}
```

| Key | Type | Meaning |
|---|---|---|
| `player` | `int` | `0` if you are A (start top-left), `1` if you are B (start bottom-right) |
| `walls` | `numpy.ndarray`, bool, `(9, 9)` | `walls[row, col]` is `True` for a wall. Never changes during a game |
| `me` | `(int, int)` | your position `(row, col)` |
| `opp` | `(int, int)` | the opponent's position |
| `bombs` | tuple of dicts | every bomb on the board, yours and the opponent's (empty if none) |
| `bombs[i]["pos"]` | `(int, int)` | the cell the bomb is on |
| `bombs[i]["owner"]` | `int` | the player who dropped it (`0` or `1`; compare with `obs["player"]`) |
| `bombs[i]["fuse"]` | `int` | steps until it explodes (1 to 5) |
| `lives` | `(int, int)` | `(your lives, the opponent's lives)` |
| `step` | `int` | how many steps have been played; the game stops at 300 |

The observation is given as it is: turning it into features, a grid, or a tensor for a neural network
is up to you. For example:

```python
row, col = obs["me"]
is_wall_above = obs["walls"][row - 1, col]
my_bombs = [b for b in obs["bombs"] if b["owner"] == obs["player"]]
cells_with_bombs = {b["pos"] for b in obs["bombs"]}
```

`legal_actions(obs)` (from `bombcompetition`) returns `STAY`, `BOMB` and every move that is not blocked
by a wall, a bomb or the opponent.

### Example bot

`examples/simple/policy.py` reads the observation and drops a bomb when the opponent is within two
cells, otherwise it walks in a random free direction. It does not look out for explosions at all, so
it often blows itself up. Start from it, or from the empty template in `submission/policy.py`.

## 4. Testing locally

```bash
python run_match.py --p1 submission --p2 examples/simple --games 20
```

plays 20 games with `--p1` as player A (top-left start) and `--p2` as player B, under the same rules
as the league, and prints,
for each bot, wins / draws / losses, kills, deaths, faults and its slowest `act` call, followed by the
first fault messages if there were any.

```bash
python run_match.py --p1 submission --p2 examples/simple --gif replay.gif
```

plays one game and saves it as an animation. Swap `--p1` and `--p2` to test your bot from the other side. You can also try your own ideas by hand
in `web/play.html`.

## 5. What you may and may not do

**You may**

- change anything inside `submission/`, and add files there (helper modules, model weights, ...);
- use any idea or algorithm: hand-written rules, search, simulation, learning, ...;
- read all the code in this repository, and use it to simulate games for your own testing or training;
- use outside code or papers, if you cite them (**TBD**: where to cite).

**You may not**

- change `bombcompetition/` or `run_match.py` to make your bot work: the league uses the official
  versions, so changes there have no effect on your result;
- access the network, write files, or interfere with the other bot or the game engine from your bot;
- use libraries other than the allowed ones: **TBD** (at least the Python standard library and numpy).

## 6. Submission

- Zip your `submission/` folder so that `policy.py` is at the top of the zip, and name it after your team:

```bash
cd submission && zip -r ../<team_name>.zip . && cd ..
```

- Upload it to **TBD** by **TBD**.
- Keep the zip small (**TBD** MB at most), and make sure it runs from a fresh copy of this repository.

## 7. Evaluation

- Every pair of teams plays **TBD** games, sides swapped every game. Each team's bot also plays the
  TA bots.
- **Ranking**: total number of kills against the other teams, together with the results against the
  TA bots. **TBD**: how the two are combined into the grade.
- A bot that cannot be loaded, or that faults, simply stays still in those steps. It is not disqualified,
  but it will probably lose.
- The league is run with `league.py` in this repository, using the same engine and fault handling as `run_match.py`.

## 8. Checklist before you submit

- [ ] `python run_match.py --p1 submission --p2 examples/simple --games 20` runs and reports **0 faults**.
- [ ] It also runs as player B: `python run_match.py --p1 examples/simple --p2 submission --games 20`.
- [ ] The slowest `act` call is well within the time limit (**TBD**).
- [ ] Everything your bot needs is inside `submission/` and loaded relative to `policy.py`.
- [ ] Your bot uses only the allowed libraries.
- [ ] The zip has `policy.py` at its top level.

## 9. Optional: reinforcement learning

`bombcompetition.BomberEnv` wraps the game as a [Gymnasium](https://gymnasium.farama.org/) environment
in which you play one side and a fixed opponent plays the other:

```python
from bombcompetition import BomberEnv, load_policy

opponent = load_policy("examples/simple")()
env = BomberEnv(opponent=opponent.act, player=0)   # player=1 to play as B
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(action)
```

- `obs` is the same dict as above; `env.observation_space` describes it as a `gymnasium.spaces.Dict`.
- The default reward is `+1` when your bomb kills the opponent and `-1` when you lose a life.
  `info["deaths"]` (who died this step and who got the kill) and `env.game` (the full game state) are
  there for building your own reward, e.g. with a `gymnasium.Wrapper`.
- The opponent can be any function `obs -> action`, including an earlier version of your own bot.
- Whatever you train, your submission still has to be a `Policy` that answers quickly (time limit **TBD**).

## Repository layout

| Path | For | What |
|---|---|---|
| `submission/policy.py` | you | your bot (the only thing you hand in) |
| `examples/simple/` | you | the example bot |
| `run_match.py` | you | play two bots under the league rules |
| `web/play.html` | you | play the game in a browser |
| `bombcompetition/` | engine | the game (`game.py`), the Gymnasium env (`env.py`), rendering, match runner. Do not change |
| `league.py` | TAs | runs the league |
| `tests/`, `tools/`, `web/template.html`, `images/` | TAs | rule tests, build scripts, sources of the web page and images |

Board sprites from [CoderOne Bomberland](https://github.com/CoderOneHQ/bomberland) (MIT,
`bombcompetition/assets/LICENSE-bomberland.md`).
