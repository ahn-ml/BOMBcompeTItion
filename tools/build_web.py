"""Build web/play.html from web/template.html by inlining the sprites.

    python tools/build_web.py

The browser game re-implements the rules in JavaScript; keep it in sync with
bombcompetition/game.py (tests/game_traces.json can be replayed against it).
"""

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "bombcompetition" / "assets"

sprites = {
    f.stem: "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode()
    for f in sorted(ASSETS.glob("*.png"))
}
template = (ROOT / "web" / "template.html").read_text()
assert "/*SPRITES*/" in template
(ROOT / "web" / "play.html").write_text(template.replace("/*SPRITES*/", json.dumps(sprites)))
print("wrote web/play.html")
