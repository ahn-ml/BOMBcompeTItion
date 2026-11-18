"""Images for README.md.

    python tools/make_images.py   # writes images/board.png and images/match.gif
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw

from bombcompetition import Game, blast_cells, load_policy
from bombcompetition.game import Bomb
from bombcompetition.render import save_gif, to_rgb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
TILE, MARGIN = 48, 28


def board_with_coordinates(game):
    board = Image.fromarray(to_rgb(game, TILE))
    bar = TILE // 2
    img = Image.new("RGB", (board.width + MARGIN, board.height + MARGIN), (18, 22, 29))
    img.paste(board, (MARGIN, 0))
    draw = ImageDraw.Draw(img)
    for i in range(game.size):
        draw.text((MARGIN // 2, bar + i * TILE + TILE // 2), str(i), fill="white", anchor="mm", font_size=14)
        draw.text((MARGIN + i * TILE + TILE // 2, img.height - MARGIN // 2), str(i), fill="white", anchor="mm", font_size=14)
    draw.text((MARGIN // 2, bar // 2), "row", fill="gray", anchor="mm", font_size=10)
    draw.text((MARGIN // 2, img.height - MARGIN // 2), "col", fill="gray", anchor="mm", font_size=10)
    return img


OUT.mkdir(exist_ok=True)
game = Game()
game.pos = [(3, 3), (5, 5)]
game.bombs = {(1, 3): Bomb(0, 4), (7, 5): Bomb(1, 2)}
game.t = 37
game.last_blast = blast_cells(game.walls, (5, 1), game.rules.radius)  # a bomb at (5, 1) just exploded
board_with_coordinates(game).save(OUT / "board.png")

random.seed(1)
bot = load_policy(ROOT / "examples" / "simple")
a, b, game = bot(), bot(), Game()
frames = [to_rgb(game, TILE)]
while not game.done and len(frames) < 120:
    game.step(a.act(game.obs(0)), b.act(game.obs(1)))
    frames.append(to_rgb(game, TILE))
save_gif(frames, OUT / "match.gif", fps=5)
print("wrote images/board.png, images/match.gif")
