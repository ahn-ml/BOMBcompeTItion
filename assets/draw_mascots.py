"""Draw 16x16 Bomberland-style mascot sprites (fan pixel art): A = Nubzuki, B = KAIST campus goose."""
import sys
from PIL import Image

PAL = {
    "O": (0x2e, 0x22, 0x2f), "W": (0xff, 0xff, 0xff),
    "B": (0x4d, 0x9b, 0xe6), "L": (0x8f, 0xd3, 0xff), "D": (0x4d, 0x65, 0xb4),  # Bomberland blues
    "R": (0xe8, 0x3b, 0x3b), "M": (0xc3, 0x24, 0x54), "N": (0x93, 0x1a, 0x4b),  # red / magenta / dark magenta
    "F": (0xfb, 0x6b, 0x1d), "Y": (0xf9, 0xc2, 0x2b),                          # orange / yellow
    "G": (0x9b, 0xab, 0xb2), "K": (0x48, 0x4a, 0x77), "P": (0xf0, 0x4f, 0x78),
    "S": (0xc7, 0xdc, 0xd0),  # light grey shading
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


def make(rows, path):
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), [len(r) for r in rows]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), PAL[ch] + (255,))
    img.save(path)


out = sys.argv[1] if len(sys.argv) > 1 else __import__("os").path.dirname(__file__)
make(NUBZUKI, f"{out}/player_a.png")
make(GOOSE, f"{out}/player_b.png")
