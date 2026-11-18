"""Play two submissions against each other.

    python run_match.py examples/greedy examples/random --games 20
    python run_match.py examples/greedy examples/random --gif match.gif

A submission is a folder with a policy.py that defines `class Policy` with `act(obs) -> int`.
"""

import argparse
import importlib.util
from pathlib import Path

from bomber_env import play_match, save_gif


def load_policy(folder):
    """Return the Policy class from <folder>/policy.py."""
    path = Path(folder) / "policy.py"
    spec = importlib.util.spec_from_file_location(f"policy_{abs(hash(str(path.resolve())))}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Policy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--gif", help="save one game as a GIF instead")
    args = ap.parse_args()
    A, B = load_policy(args.a), load_policy(args.b)

    if args.gif:
        w = save_gif(A().act, B().act, args.gif)
        print(f"saved {args.gif}, winner: {['A', 'B'][w] if w is not None else 'draw'}")
        return

    wins, kills = {"a": 0, "b": 0, None: 0}, {"a": 0, "b": 0}
    for i in range(args.games):  # swap sides every game
        sides = ("a", "b") if i % 2 == 0 else ("b", "a")
        pols = {"a": A, "b": B}
        g = play_match(pols[sides[0]]().act, pols[sides[1]]().act)
        w = g.winner()
        wins[sides[w] if w is not None else None] += 1
        for p in (0, 1):
            kills[sides[p]] += g.kills[p]
    print(f"{args.a}: {wins['a']} wins, {kills['a']} kills | "
          f"{args.b}: {wins['b']} wins, {kills['b']} kills | draws: {wins[None]}")


if __name__ == "__main__":
    main()
