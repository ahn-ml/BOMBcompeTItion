"""The class league.

    python league.py --teams submissions --ta ta_bots --games 10

Every pair of teams, and every team against every TA bot, plays --games games
(sides swapped each game). Teams are listed by total kills against other teams.
"""

import argparse
import csv
import itertools
from dataclasses import asdict
from pathlib import Path

from bombcompetition import load_policy, play_series

ap = argparse.ArgumentParser()
ap.add_argument("--teams", required=True, help="one folder with policy.py per team")
ap.add_argument("--ta", required=True, help="one folder with policy.py per TA bot")
ap.add_argument("--games", type=int, default=10)
ap.add_argument("--out", default="league_results.csv")
args = ap.parse_args()


def bots(root):
    return {d.name: load_policy(d) for d in sorted(Path(root).iterdir()) if (d / "policy.py").exists()}


teams, tas = bots(args.teams), bots(args.ta)
rows = []  # (stage, team, opponent, Record)
for a, b in itertools.combinations(teams, 2):
    ra, rb = play_series(teams[a], teams[b], args.games)
    rows += [("teams", a, b, ra), ("teams", b, a, rb)]
for team, ta in itertools.product(teams, tas):
    rows.append(("ta", team, ta, play_series(teams[team], tas[ta], args.games)[0]))

with open(args.out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["stage", "team", "opponent", "kills", "deaths", "wins", "draws", "losses", "faults"])
    for stage, team, opp, r in rows:
        w.writerow([stage, team, opp, r.kills, r.deaths, r.wins, r.draws, r.losses, r.faults])


def total(team, stage, key):
    return sum(asdict(r)[key] for s, t, _, r in rows if t == team and s == stage)


print(f"{'team':<20}{'kills':>6}{'deaths':>7}   {'vs TA W/D/L':>11}{'faults':>7}")
for team in sorted(teams, key=lambda t: -total(t, "teams", "kills")):
    wdl = "/".join(str(total(team, "ta", k)) for k in ("wins", "draws", "losses"))
    faults = total(team, "teams", "faults") + total(team, "ta", "faults")
    print(f"{team:<20}{total(team, 'teams', 'kills'):>6}{total(team, 'teams', 'deaths'):>7}   {wdl:>11}{faults:>7}")
print(f"\nsaved {args.out}")
