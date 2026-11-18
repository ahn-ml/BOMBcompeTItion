"""Play two bots against each other under the league rules. A bot is a folder with policy.py.

    python run_match.py --p1 submission --p2 examples/simple --games 20
    python run_match.py --p1 submission --p2 examples/simple --gif replay.gif

--p1 always plays A (starts top-left), --p2 always plays B (starts bottom-right).
"""

import argparse

from bombcompetition import load_policy, play_match, play_series

ap = argparse.ArgumentParser(description="Play two bots against each other. Each bot is a folder with policy.py.")
ap.add_argument("--p1", required=True, help="bot folder for player 1 (A, starts top-left), e.g. submission")
ap.add_argument("--p2", required=True, help="bot folder for player 2 (B, starts bottom-right), e.g. examples/simple")
ap.add_argument("--games", type=int, default=10, help="number of games")
ap.add_argument("--gif", help="instead, play one game and save it as a GIF")
args = ap.parse_args()
p1, p2 = load_policy(args.p1), load_policy(args.p2)

if args.gif:
    game = play_match(p1().act, p2().act, gif=args.gif)
    print(f"saved {args.gif}  kills {game.kills[0]}:{game.kills[1]}  lives {game.lives[0]}:{game.lives[1]}")
else:
    for name, r in zip((f"p1 {args.p1}", f"p2 {args.p2}"), play_series(p1, p2, args.games, swap=False)):
        print(f"{name}: {r.wins}W {r.draws}D {r.losses}L  kills {r.kills}  deaths {r.deaths}  "
              f"faults {r.faults}  slowest act {r.slowest * 1000:.0f} ms")
        for e in dict.fromkeys(r.errors):
            print("   fault:", e)
