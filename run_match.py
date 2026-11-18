"""Play two bots against each other.

    python run_match.py examples/greedy examples/simple --games 20
    python run_match.py examples/greedy examples/simple --gif match.gif

A bot is a folder with policy.py defining `class Policy` with `act(obs) -> int`.
"""

import argparse

from bombcompetition import load_policy, play_match


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bot_a")
    ap.add_argument("bot_b")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--gif", help="play one game (bot_a as A) and save it as a GIF")
    args = ap.parse_args()
    names = (args.bot_a, args.bot_b)
    bots = [load_policy(n) for n in names]

    if args.gif:
        game = play_match(bots[0]().act, bots[1]().act, gif=args.gif)
        print(f"saved {args.gif}: kills {game.kills[0]}:{game.kills[1]}, lives {game.lives[0]}:{game.lives[1]}")
        return

    wins, kills, draws = [0, 0], [0, 0], 0
    for i in range(args.games):
        order = (0, 1) if i % 2 == 0 else (1, 0)  # swap sides every game
        game = play_match(bots[order[0]]().act, bots[order[1]]().act)
        for side, bot in enumerate(order):
            kills[bot] += game.kills[side]
        w = game.winner()
        if w is None:
            draws += 1
        else:
            wins[order[w]] += 1
    for n, w, k in zip(names, wins, kills):
        print(f"{n:<30} wins {w:>4}   kills {k:>4}")
    print(f"{'draws':<30} {draws:>9}")


if __name__ == "__main__":
    main()
