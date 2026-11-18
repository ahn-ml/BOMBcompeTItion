"""Draw a game as text or as an RGB image.

Tiles, bombs and the explosion are sprites from CoderOne Bomberland (MIT, see
assets/LICENSE-bomberland.md); the characters are drawn by tools/draw_mascots.py.
"""

from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .game import Game

ASSETS = Path(__file__).parent / "assets"
SPRITE = 16  # sprite size in pixels
BACKGROUND = (18, 22, 29)


def to_text(game: Game) -> str:
    grid = [["#" if w else "." for w in row] for row in game.walls]
    for r, c in game.last_blast:
        grid[r][c] = "*"
    for (r, c), bomb in game.bombs.items():
        grid[r][c] = str(min(bomb.fuse, 9))
    for p, name in enumerate("AB"):
        r, c = game.pos[p]
        grid[r][c] = name
    head = f"t={game.t} lives A={game.lives[0]} B={game.lives[1]} kills A={game.kills[0]} B={game.kills[1]}"
    return "\n".join([head] + ["".join(row) for row in grid])


@cache
def _sprites(scale: int) -> dict[str, Image.Image]:
    size = (SPRITE * scale, SPRITE * scale)
    return {f.stem: Image.open(f).convert("RGBA").resize(size, Image.NEAREST) for f in ASSETS.glob("*.png")}


def to_rgb(game: Game, scale: int = 4) -> np.ndarray:
    """RGB image (H, W, 3): a status bar on top of the board."""
    sprites = _sprites(scale)
    tile = SPRITE * scale
    bar = tile // 2
    img = Image.new("RGB", (game.size * tile, bar + game.size * tile), BACKGROUND)

    def put(name, r, c):
        img.paste(sprites[name], (c * tile, bar + r * tile), sprites[name])

    for r in range(game.size):
        for c in range(game.size):
            put(f"floor_{(r * 7 + c * 3) % 5 + 1}", r, c)
            if game.walls[r, c]:
                put("wall", r, c)
            if (r, c) in game.last_blast:
                put("blast", r, c)
    draw = ImageDraw.Draw(img)
    for (r, c), bomb in game.bombs.items():
        put("bomb_" + "ab"[bomb.owner], r, c)
        draw.text((c * tile + tile - 4, bar + r * tile + 2), str(bomb.fuse), fill="white", anchor="ra", font_size=tile // 3)
    for p in (0, 1):
        put("player_" + "ab"[p], *game.pos[p])

    status = (
        f"A  lives {game.lives[0]}  kills {game.kills[0]}      "
        f"t = {game.t} / {game.rules.max_steps}      "
        f"kills {game.kills[1]}  lives {game.lives[1]}  B"
    )
    draw.text((img.width // 2, bar // 2), status, fill="white", anchor="mm", font_size=bar * 2 // 3)
    return np.asarray(img)


def save_gif(frames: list[np.ndarray], path: str | Path, fps: int = 4):
    images = [Image.fromarray(f) for f in frames]
    images[0].save(path, save_all=True, append_images=images[1:], duration=1000 // fps, loop=0)
