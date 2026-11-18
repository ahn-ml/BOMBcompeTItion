"""Play two bots against each other under the league rules and time limits.

    python run_match.py submission examples/random --games 20
    python run_match.py submission examples/random --gif replay.gif

A bot is a folder with policy.py. No faults here means it is a valid submission.
"""

import argparse

from bombcompetition import load_policy, play_match, play_series

ap = argparse.ArgumentParser()
ap.add_argument("bot_a")
ap.add_argument("bot_b")
ap.add_argument("--games", type=int, default=10)
ap.add_argument("--gif", help="instead, play one game (bot_a as A) and save it as a GIF")
args = ap.parse_args()
bots = load_policy(args.bot_a), load_policy(args.bot_b)

if args.gif:
    game = play_match(bots[0]().act, bots[1]().act, gif=args.gif)
    print(f"saved {args.gif}  kills {game.kills[0]}:{game.kills[1]}  lives {game.lives[0]}:{game.lives[1]}")
else:
    for name, r in zip((args.bot_a, args.bot_b), play_series(*bots, args.games)):
        print(f"{name}: {r.wins}W {r.draws}D {r.losses}L  kills {r.kills}  deaths {r.deaths}  "
              f"faults {r.faults}  slowest act {r.slowest * 1000:.0f} ms")
        for e in dict.fromkeys(r.errors):
            print("   fault:", e)
