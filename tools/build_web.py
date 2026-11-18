"""Build web/replay.html (the replay viewer) from web/template.html by inlining the sprites.

    python tools/build_web.py
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
(ROOT / "web" / "replay.html").write_text(template.replace("/*SPRITES*/", json.dumps(sprites)).replace("/*REPLAY*/", ""))
print("wrote web/replay.html")
