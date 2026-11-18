"""Run the class league.

    python league.py --teams submissions --ta ta_bots --games 10

--teams: folder with one sub-folder per team, each holding policy.py (+ optional weight files).
--ta:    folder with the TA bots, same layout.
Every pair of teams plays `--games` games (sides swapped each game), and every team plays
`--games` games against every TA bot. A kill counts only when your bomb kills the opponent.

Safety: `__init__` gets INIT_TIMEOUT s and `act` gets ACT_TIMEOUT s; a timeout, an exception or
an invalid action makes the player stay for that step and is counted as a fault.
"""

import argparse
import csv
import itertools
import signal
from pathlib import Path

from bomber_env import Game, STAY
from run_match import load_policy

ACT_TIMEOUT = 0.1
INIT_TIMEOUT = 10.0


def _alarm(_signum, _frame):
    raise TimeoutError


def call_with_timeout(fn, seconds, *args):
    # ponytail: SIGALRM is Unix-only and cannot interrupt long C calls; use a subprocess per bot if that matters
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return fn(*args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


class SafeBot:
    def __init__(self, cls):
        self.faults = 0
        try:
            self.policy = call_with_timeout(cls, INIT_TIMEOUT)
        except Exception:
            self.policy, self.faults = None, 1

    def act(self, obs):
        if self.policy is None:
            return STAY
        try:
            a = int(call_with_timeout(self.policy.act, ACT_TIMEOUT, obs))
            if 0 <= a <= 5:
                return a
        except Exception:
            pass
        self.faults += 1
        return STAY


def play(cls0, cls1, games):
    """Returns per-side totals {kills, deaths, wins, draws, faults} for cls0 and cls1."""
    tot = [dict(kills=0, deaths=0, wins=0, draws=0, faults=0) for _ in range(2)]
    for i in range(games):
        order = (0, 1) if i % 2 == 0 else (1, 0)  # order[p] = which of cls0/cls1 plays side p
        bots = [SafeBot((cls0, cls1)[order[p]]) for p in (0, 1)]
        g = Game()
        while not g.done:
            g.step(bots[0].act(g.obs(0)), bots[1].act(g.obs(1)))
        w = g.winner()
        for p in (0, 1):
            t = tot[order[p]]
            t["kills"] += g.kills[p]
            t["deaths"] += g.max_lives - g.lives[p]
            t["wins"] += w == p
            t["draws"] += w is None
            t["faults"] += bots[p].faults
    return tot


def folders(root):
    return sorted(d for d in Path(root).iterdir() if (d / "policy.py").exists())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teams", required=True)
    ap.add_argument("--ta", required=True)
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--out", default="league_results.csv")
    args = ap.parse_args()

    teams = {d.name: load_policy(d) for d in folders(args.teams)}
    tas = {d.name: load_policy(d) for d in folders(args.ta)}
    rows = []  # (stage, team, opponent, kills, deaths, wins, draws, losses, faults)

    for a, b in itertools.combinations(teams, 2):
        ta, tb = play(teams[a], teams[b], args.games)
        for name, opp, t in ((a, b, ta), (b, a, tb)):
            rows.append(("teams", name, opp, t["kills"], t["deaths"], t["wins"], t["draws"],
                         args.games - t["wins"] - t["draws"], t["faults"]))
        print(f"{a} vs {b}: kills {ta['kills']}:{tb['kills']}")
    for name, bot in itertools.product(teams, tas):
        t, _ = play(teams[name], tas[bot], args.games)
        rows.append(("ta", name, bot, t["kills"], t["deaths"], t["wins"], t["draws"],
                     args.games - t["wins"] - t["draws"], t["faults"]))
        print(f"{name} vs TA {bot}: W/D/L {t['wins']}/{t['draws']}/{args.games - t['wins'] - t['draws']}")

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stage", "team", "opponent", "kills", "deaths", "wins", "draws", "losses", "faults"])
        w.writerows(rows)

    print(f"\n{'team':<16}{'team kills':>11}{'deaths':>8}{'TA W/D/L':>12}{'TA kills':>10}{'faults':>8}")
    for name in sorted(teams, key=lambda n: -sum(r[3] for r in rows if r[0] == "teams" and r[1] == n)):
        mine = [r for r in rows if r[1] == name]
        tk = sum(r[3] for r in mine if r[0] == "teams")
        td = sum(r[4] for r in mine if r[0] == "teams")
        ta = [r for r in mine if r[0] == "ta"]
        wdl = "/".join(str(sum(r[i] for r in ta)) for i in (5, 6, 7))
        print(f"{name:<16}{tk:>11}{td:>8}{wdl:>12}{sum(r[3] for r in ta):>10}{sum(r[8] for r in mine):>8}")
    print(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()
