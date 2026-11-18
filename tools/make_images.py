"""Images for README.md.

    python tools/make_images.py   # writes images/board.png and images/match.gif
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw

from bombcompetition import DELTAS, Action, Game, blast_cells, legal_actions
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



def busy_bot(obs):
    """Drops bombs often and steps out of blast ranges: only for a lively demo GIF."""
    mine = [b for b in obs["bombs"] if b["owner"] == obs["player"]]
    if len(mine) < 2 and random.random() < 0.35:
        return Action.BOMB
    danger = set()
    for bomb in obs["bombs"]:
        danger |= blast_cells(obs["walls"], bomb["pos"], 2)
    moves = [a for a in legal_actions(obs) if a != Action.BOMB]
    r, c = obs["me"]
    safe = [a for a in moves if (r + DELTAS[a][0], c + DELTAS[a][1]) not in danger]
    return random.choice(safe or moves)


def demo_game(seed, length=100):
    random.seed(seed)
    game, frames, explosions, kills = Game(), [], 0, 0
    frames.append(to_rgb(game, TILE))
    while not game.done and len(frames) < length:
        deaths = game.step(busy_bot(game.obs(0)), busy_bot(game.obs(1)))
        explosions += bool(game.last_blast)
        kills += sum(d.killer is not None for d in deaths)
        frames.append(to_rgb(game, TILE))
    return frames, explosions + 5 * kills


frames = max((demo_game(seed) for seed in range(100)), key=lambda x: (len(x[0]) == 101, x[1]))[0]
save_gif(frames, OUT / "match.gif", fps=5)
print("wrote images/board.png, images/match.gif")
