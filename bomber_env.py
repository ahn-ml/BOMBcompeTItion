"""Mini Bomberman: 1v1 on a fixed map with bombs and fixed walls only.

Rules you can change (keyword arguments of Game / BomberEnv / play_match / save_gif):
  layout="rooms"  map name in MAPS or your own list of strings ('#' wall, '.' floor, 'A'/'B' starts)
  starts=None     ((row, col), (row, col)) start cells of A and B, overriding 'A'/'B' in the layout
  fuse=6          steps until a placed bomb explodes
  radius=2        explosion length in each direction
  max_bombs=2     bombs a player may have on the map at once
  lives=3, max_steps=300

One step = both players act at the same time:
  1. Bomb: place a bomb on your own cell (at most `max_bombs` of yours at once).
  2. Move: blocked by walls, bombs, and the other player's current cell.
     If both players move into the same cell, neither moves.
  3. Every bomb's fuse goes down by 1. At 0 it explodes in a cross of length
     `radius`, stopped by walls. Explosions set off other bombs (chain).
     A player inside an explosion loses a life (your own bomb counts too).
  4. If anyone lost a life, the round restarts: both players go back to their
     start cells and all bombs are removed.
  The game ends when someone has no lives left or after `max_steps`.
  Winner: the player with more lives left (= more kills). Equal = draw.

Observation: the same board coordinates for both players (no rotation; row 0 is
the top). Player 0 is A (starts top-left on the default maps), player 1 is B.
  float32 array, shape (9, size, size)
    0 walls   1 me   2 opponent   3 my bombs (fuse / FUSE)   4 opponent bombs (fuse / FUSE)
    5 my lives / LIVES   6 opponent lives / LIVES   7 steps left / max_steps
    8 which player I am: 0.0 = A (player 0), 1.0 = B (player 1)      (5-8: constant planes)
Actions (absolute directions on the board): 0 stay, 1 up, 2 down, 3 left, 4 right, 5 bomb
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces

MAPS = {
    "rooms": [
        "#########",
        "#A..#...#",
        "#.#.#.#.#",
        "#.#...#.#",
        "#...#...#",
        "#.#...#.#",
        "#.#.#.#.#",
        "#...#..B#",
        "#########",
    ],
    "pillar": [
        "#########",
        "#A......#",
        "#.#.#.#.#",
        "#.......#",
        "#.#.#.#.#",
        "#.......#",
        "#.#.#.#.#",
        "#......B#",
        "#########",
    ],
}

STAY, UP, DOWN, LEFT, RIGHT, BOMB = range(6)
DELTAS = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
N_CHANNELS = 9


class Game:
    """Two-player game. Players are 0 and 1. All positions are (row, col)."""

    def __init__(self, layout="rooms", starts=None, max_bombs=2, fuse=6, radius=2, lives=3, max_steps=300):
        """
        layout: a name in MAPS, or a list of equal-length strings of a square map
                ('#' wall, '.' floor, 'A'/'B' start cells). The border must be all walls.
        starts: ((row, col), (row, col)) for players A and B; overrides 'A'/'B' in the layout.
        fuse:   steps from placing a bomb until it explodes.
        radius: how many cells the explosion reaches in each of the 4 directions.
        """
        rows = MAPS[layout] if isinstance(layout, str) else list(layout)
        self.size = len(rows)
        assert all(len(row) == self.size for row in rows), "map must be square"
        self.walls = np.array([[ch == "#" for ch in row] for row in rows])
        border = np.ones_like(self.walls)
        border[1:-1, 1:-1] = False
        assert self.walls[border].all(), "map border must be all walls"
        if starts is None:
            starts = [next((r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == x) for x in "AB"]
        self.starts = [tuple(s) for s in starts]
        assert self.starts[0] != self.starts[1] and not any(self.walls[s] for s in self.starts), "bad start cells"
        assert fuse >= 1 and radius >= 0 and max_bombs >= 1 and lives >= 1
        self.max_bombs, self.fuse, self.radius = max_bombs, fuse, radius
        self.max_lives, self.max_steps = lives, max_steps
        self.lives = [lives, lives]
        self.kills = [0, 0]  # kills[p]: times p's bomb killed the other player (suicides don't count)
        self.t = 0
        self.done = False
        self.reset_round()

    def reset_round(self):
        self.pos = list(self.starts)
        self.bombs = {}  # (r, c) -> [owner, fuse]
        self.last_blast = set()

    def blast_cells(self, r, c):
        """Cells hit by a bomb at (r, c): a cross that stops at walls."""
        cells = {(r, c)}
        for dr, dc in DELTAS[1:5]:
            for k in range(1, self.radius + 1):
                cell = (r + dr * k, c + dc * k)
                if self.walls[cell]:
                    break
                cells.add(cell)
        return cells

    def step(self, a0, a1):
        """Advance one step. Returns the list of players who lost a life."""
        assert not self.done, "game is over"
        actions = (int(a0), int(a1))
        # 1. bombs
        for p, a in enumerate(actions):
            mine = sum(owner == p for owner, _ in self.bombs.values())
            if a == BOMB and mine < self.max_bombs and self.pos[p] not in self.bombs:
                self.bombs[self.pos[p]] = [p, self.fuse]
        # 2. moves
        targets = []
        for p, a in enumerate(actions):
            (r, c), (dr, dc) = self.pos[p], DELTAS[a]
            t = (r + dr, c + dc)
            if self.walls[t] or (t != self.pos[p] and t in self.bombs) or t == self.pos[1 - p]:
                t = self.pos[p]
            targets.append(t)
        if targets[0] != targets[1]:
            self.pos = targets
        # 3. fuses and chained explosions
        for b in self.bombs.values():
            b[1] -= 1
        blast = set()
        hit_by = [set(), set()]  # owners of the bombs whose explosion reached each player
        queue = [cell for cell, (_, fuse) in self.bombs.items() if fuse <= 0]
        while queue:
            cell = queue.pop()
            bomb = self.bombs.pop(cell, None)
            if bomb is None:
                continue
            hit = self.blast_cells(*cell)
            blast |= hit
            queue += [x for x in hit if x in self.bombs]
            for p in (0, 1):
                if self.pos[p] in hit:
                    hit_by[p].add(bomb[0])
        hurt = [p for p in (0, 1) if self.pos[p] in blast]
        for p in hurt:
            self.lives[p] -= 1
            if 1 - p in hit_by[p]:
                self.kills[1 - p] += 1
        self.t += 1
        self.done = min(self.lives) <= 0 or self.t >= self.max_steps
        # 4. new round after a death
        if hurt and not self.done:
            self.reset_round()
        self.last_blast = blast
        return hurt

    def winner(self):
        """0 or 1 for the player with more lives left, None for a draw."""
        if self.lives[0] == self.lives[1]:
            return None
        return 0 if self.lives[0] > self.lives[1] else 1

    def obs(self, p):
        o = np.zeros((N_CHANNELS, self.size, self.size), dtype=np.float32)
        o[0] = self.walls
        o[1][self.pos[p]] = 1
        o[2][self.pos[1 - p]] = 1
        for cell, (owner, fuse) in self.bombs.items():
            o[3 if owner == p else 4][cell] = fuse / self.fuse
        o[5] = self.lives[p] / self.max_lives
        o[6] = self.lives[1 - p] / self.max_lives
        o[7] = (self.max_steps - self.t) / self.max_steps
        o[8] = p
        return o

    def render(self):
        grid = [["#" if w else "." for w in row] for row in self.walls]
        for r, c in self.last_blast:
            grid[r][c] = "*"
        for (r, c), (_, fuse) in self.bombs.items():
            grid[r][c] = str(min(fuse, 9))
        for p, name in enumerate("AB"):
            r, c = self.pos[p]
            grid[r][c] = name
        head = f"t={self.t} lives A={self.lives[0]} B={self.lives[1]}"
        return head + "\n" + "\n".join("".join(row) for row in grid)

    def render_rgb(self, scale=4):
        """RGB image (H, W, 3) drawn with the original Bomberland sprites."""
        from PIL import Image, ImageDraw

        tile = 16 * scale
        sprites = _sprites(scale)
        img = Image.new("RGB", (self.size * tile, self.size * tile + tile // 2), (18, 22, 29))
        top = tile // 2
        for r in range(self.size):
            for c in range(self.size):
                xy = (c * tile, top + r * tile)
                img.paste(sprites[f"floor_{(r * 7 + c * 3) % 5 + 1}"], xy)
                if self.walls[r, c]:
                    img.paste(sprites["wall"], xy, sprites["wall"])
                if (r, c) in self.last_blast:
                    img.paste(sprites["blast"], xy, sprites["blast"])
        draw = ImageDraw.Draw(img)
        for (r, c), (owner, fuse) in self.bombs.items():
            s = sprites["bomb_" + "ab"[owner]]
            img.paste(s, (c * tile, top + r * tile), s)
            draw.text((c * tile + tile - 4, top + r * tile + 2), str(fuse), fill="white", anchor="ra", font_size=tile // 3)
        for p in (0, 1):
            r, c = self.pos[p]
            s = sprites["player_" + "ab"[p]]
            img.paste(s, (c * tile, top + r * tile), s)
        hud = f"A  lives {self.lives[0]}      t = {self.t} / {self.max_steps}      lives {self.lives[1]}  B"
        draw.text((img.width // 2, top // 2), hud, fill="white", anchor="mm", font_size=top * 2 // 3)
        return np.asarray(img)


_SPRITE_CACHE = {}


def _sprites(scale):
    """Sprites from CoderOne Bomberland (MIT, see assets/LICENSE-bomberland.md), upscaled pixel-perfect."""
    if scale not in _SPRITE_CACHE:
        from pathlib import Path
        from PIL import Image

        folder = Path(__file__).parent / "assets"
        _SPRITE_CACHE[scale] = {
            f.stem: Image.open(f).convert("RGBA").resize((16 * scale, 16 * scale), Image.NEAREST)
            for f in folder.glob("*.png")
        }
    return _SPRITE_CACHE[scale]


def play_match(act0, act1, render=False, **rules):
    """Play one game between two policies (obs -> action). Returns the finished Game
    (see .kills, .lives, .winner())."""
    g = Game(**rules)
    while not g.done:
        g.step(int(act0(g.obs(0))), int(act1(g.obs(1))))
        if render:
            print(g.render(), end="\n\n")
    return g


def save_gif(act0, act1, path, fps=4, scale=4, **rules):
    """Play one game and save it as an animated GIF. Returns the winner."""
    from PIL import Image

    g = Game(**rules)
    frames = [g.render_rgb(scale)]
    while not g.done:
        g.step(int(act0(g.obs(0))), int(act1(g.obs(1))))
        frames.append(g.render_rgb(scale))
    imgs = [Image.fromarray(f) for f in frames]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=1000 // fps, loop=0)
    return g.winner()


def random_policy(obs):
    return np.random.randint(6)


class BomberEnv(gym.Env):
    """Single-agent view of the game: you are `player` (0 = A, 1 = B), `opponent` (obs -> action) is the other.

    Reward per step: +1 when your bomb kills the opponent, -1 when you lose a life
    (to any bomb, including your own).
    """

    metadata = {"render_modes": ["ansi", "rgb_array"], "render_fps": 4}

    def __init__(self, opponent=random_policy, player=0, render_mode=None, **rules):
        self.opponent = opponent
        self.player = player
        self.rules = rules
        self.render_mode = render_mode
        size = Game(**rules).size  # also validates the rules early
        self.observation_space = spaces.Box(0.0, 1.0, (N_CHANNELS, size, size), np.float32)
        self.action_space = spaces.Discrete(6)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            np.random.seed(seed)
        self.game = Game(**self.rules)
        return self.game.obs(self.player), {}

    def step(self, action):
        g = self.game
        me, opp = self.player, 1 - self.player
        acts = [0, 0]
        acts[me], acts[opp] = int(action), int(self.opponent(g.obs(opp)))
        kills_before = g.kills[me]
        hurt = g.step(*acts)
        reward = float(g.kills[me] - kills_before - (me in hurt))
        terminated = min(g.lives) <= 0
        truncated = g.done and not terminated
        info = {"lives": tuple(g.lives), "winner": g.winner() if g.done else None}
        return g.obs(me), reward, terminated, truncated, info

    def render(self):
        if self.render_mode == "rgb_array":
            return self.game.render_rgb()
        return self.game.render()


if __name__ == "__main__":
    from gymnasium.utils.env_checker import check_env

    check_env(BomberEnv())

    # rule checks
    g = Game(lives=1)
    g.step(BOMB, STAY)
    assert g.pos[0] in g.bombs and g.bombs[g.pos[0]] == [0, g.fuse - 1]
    g.step(DOWN, STAY)
    g.step(UP, STAY)  # cannot walk back onto own bomb
    assert g.pos[0] == (2, 1), g.pos
    for _ in range(g.fuse - 3):
        g.step(STAY, STAY)
    assert g.done and g.lives == [0, 1] and g.winner() == 1, "own bomb must kill"
    assert g.kills == [0, 0], "suicide is not a kill"

    g = Game(lives=1)
    g.pos = [(1, 3), (3, 1)]
    g.bombs = {(1, 1): [0, 1]}  # A's bomb hits B at (3, 1); A at (1, 3) is hit too
    g.step(STAY, STAY)
    assert g.lives == [0, 0] and g.kills == [1, 0]

    g = Game()
    g.pos = [(4, 1), (4, 3)]
    g.step(RIGHT, LEFT)  # both target (4, 2): nobody moves
    assert g.pos == [(4, 1), (4, 3)]

    g = Game()
    assert g.blast_cells(1, 1) == {(1, 1), (1, 2), (1, 3), (2, 1), (3, 1)}  # (1, 4) is a wall

    # custom map, starts and bomb rules
    tiny = ["#######", "#.....#", "#.#.#.#", "#.....#", "#######"]
    g = Game(layout=["#####", "#...#", "#...#", "#...#", "#####"], starts=((1, 1), (3, 3)), fuse=2, radius=1, lives=1)
    assert g.size == 5 and g.pos == [(1, 1), (3, 3)]
    g.step(BOMB, STAY)
    g.step(STAY, STAY)
    assert g.done and g.winner() == 1, "fuse=2 bomb explodes on the 2nd step"
    assert Game(radius=1).blast_cells(1, 1) == {(1, 1), (1, 2), (2, 1)}
    env = BomberEnv(layout=["#####", "#A..#", "#...#", "#..B#", "#####"])
    assert env.reset()[0].shape == (N_CHANNELS, 5, 5)
    check_env(env)
    for bad in (dict(layout=tiny), dict(starts=((0, 0), (3, 3))), dict(starts=((1, 1), (1, 1)))):
        try:
            Game(**bad)
            raise SystemExit(f"should reject {bad}")
        except AssertionError:
            pass

    # no rotation: both players see the same board, channel 8 says who you are
    o0, o1 = Game().obs(0), Game().obs(1)
    assert o0[1, 1, 1] == 1 and o1[2, 1, 1] == 1 and o1[1, 7, 7] == 1
    assert o0[8].max() == 0 and o1[8].min() == 1 and (o0[0] == o1[0]).all()
    env = BomberEnv(player=1)
    assert env.reset()[0][1, 7, 7] == 1
    check_env(env)

    wins = [play_match(random_policy, random_policy).winner() for _ in range(300)]
    print("random vs random: A", wins.count(0), "B", wins.count(1), "draw", wins.count(None))
    print("ok")
