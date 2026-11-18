"""Draw the two characters as 16x16 pixel art in the style of the board sprites.

    python tools/draw_mascots.py   # writes bombcompetition/assets/player_a.png and player_b.png

A = Nubzuki (KAIST mascot), B = KAIST campus goose. Edit the pixel grids below and rerun.
"""

from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "bombcompetition" / "assets"

PALETTE = {
    "O": (0x2E, 0x22, 0x2F),  # outline
    "W": (0xFF, 0xFF, 0xFF),  # white
    "S": (0xC7, 0xDC, 0xD0),  # light grey shading
    "B": (0x4D, 0x9B, 0xE6),  # blue
    "L": (0x8F, 0xD3, 0xFF),  # light blue
    "D": (0x4D, 0x65, 0xB4),  # dark blue
    "F": (0xFB, 0x6B, 0x1D),  # orange
}

NUBZUKI = [
    "................",
    "....OOOOOOO.....",
    "..OOLLLBBBBOO...",
    ".OLLBBBBBBBBBO..",
    ".OLBBBBBBBBBBBO.",
    "OLBBWWBBBBBWWBBO",
    "OBBWWOWBBBWWOWBO",
    "OBBWOOWBBBWOOWBO",
    "OBBBWWBBBBBWWBDO",
    ".OBBBBBBBBBBBDO.",
    "..OODDDDDDDDOO..",
    "...OOBWBWBWBOO..",
    "..OBOBBBBBBBOBO.",
    "..OOOBBBBBBBOOO.",
    "....OBBOOOBBO...",
    "....OOO...OOO...",
]

GOOSE = [
    "................",
    "....OOOO........",
    "...OWWWWO.......",
    "..OWOWWWWO......",
    "OOFFWWWWWO......",
    "OFFFOWWWO.......",
    ".OOO.OWWO.......",
    ".....OWWO.......",
    ".....OWWWOOOO...",
    "....OWWWWWWWWOO.",
    "...OWWWWWWSSWWWO",
    "...OWWWWWSSWWWWO",
    "...OSWWWWWWWWWSO",
    "....OSSSSSSSSSO.",
    "......OFO.OFO...",
    ".....OFFO.OFFO..",
]


def draw(rows, path):
    assert len(rows) == 16 and all(len(r) == 16 for r in rows)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), PALETTE[ch] + (255,))
    img.save(path)


if __name__ == "__main__":
    draw(NUBZUKI, OUT / "player_a.png")
    draw(GOOSE, OUT / "player_b.png")
    print(f"wrote {OUT}/player_a.png, player_b.png")
