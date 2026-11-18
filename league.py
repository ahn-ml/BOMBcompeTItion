"""Run the class league.

    python league.py --teams submissions --ta ta_bots --games 10

--teams  one sub-folder per team, each with policy.py (+ optional files it loads)
--ta     the TA bots, same layout

Every pair of teams plays --games games and every team plays --games games against
every TA bot, swapping sides each game. Results are printed and saved as CSV.

A bot gets INIT_TIMEOUT seconds for Policy() and ACT_TIMEOUT seconds per act().
A timeout, an exception or an invalid action makes it stay for that step (a "fault").
"""

import argparse
import csv
import itertools
import signal
from dataclasses import asdict, dataclass
from pathlib import Path

from bombcompetition import Action, Game, load_policy

ACT_TIMEOUT = 0.1
INIT_TIMEOUT = 10.0


@dataclass
class Result:
    stage: str      # "teams" or "ta"
    team: str
    opponent: str
    kills: int = 0
    deaths: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    faults: int = 0


def _raise_timeout(signum, frame):
    raise TimeoutError


def call_with_timeout(fn, seconds, *args):
    # ponytail: SIGALRM is Unix-only and cannot stop a long C call (e.g. inside torch);
    # run each bot in its own process if that becomes a problem.
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return fn(*args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


class SafeBot:
    """Wraps a submitted Policy so that it can never crash or stall the league."""

    def __init__(self, policy_cls):
        self.faults = 0
        try:
            self.policy = call_with_timeout(policy_cls, INIT_TIMEOUT)
        except Exception:
            self.policy = None
            self.faults += 1

    def act(self, obs):
        if self.policy is not None:
            try:
                action = int(call_with_timeout(self.policy.act, ACT_TIMEOUT, obs))
                if action in Action._value2member_map_:
                    return action
            except Exception:
                pass
        self.faults += 1
        return Action.STAY


def play_series(stage, names, classes, games):
    """Play `games` games between two bots; returns one Result per bot."""
    results = [Result(stage, names[0], names[1]), Result(stage, names[1], names[0])]
    for i in range(games):
        order = (0, 1) if i % 2 == 0 else (1, 0)  # order[side] = index of the bot playing that side
        bots = [SafeBot(classes[order[side]]) for side in (0, 1)]
        game = Game()
        while not game.done:
            game.step(bots[0].act(game.obs(0)), bots[1].act(game.obs(1)))
        winner = game.winner()
        for side in (0, 1):
            r = results[order[side]]
            r.kills += game.kills[side]
            r.deaths += game.rules.lives - game.lives[side]
            r.faults += bots[side].faults
            r.wins += winner == side
            r.draws += winner is None
            r.losses += winner == 1 - side
    return results


def bot_folders(root):
    return {d.name: load_policy(d) for d in sorted(Path(root).iterdir()) if (d / "policy.py").exists()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teams", required=True)
    ap.add_argument("--ta", required=True)
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--out", default="league_results.csv")
    args = ap.parse_args()
    teams, tas = bot_folders(args.teams), bot_folders(args.ta)

    results = []
    for a, b in itertools.combinations(teams, 2):
        ra, rb = play_series("teams", (a, b), (teams[a], teams[b]), args.games)
        results += [ra, rb]
        print(f"{a} vs {b}: kills {ra.kills}:{rb.kills}")
    for team, ta in itertools.product(teams, tas):
        r, _ = play_series("ta", (team, ta), (teams[team], tas[ta]), args.games)
        results.append(r)
        print(f"{team} vs TA {ta}: W/D/L {r.wins}/{r.draws}/{r.losses}, kills {r.kills}")

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0])))
        writer.writeheader()
        writer.writerows(asdict(r) for r in results)

    def total(team, stage, field):
        return sum(getattr(r, field) for r in results if r.team == team and r.stage == stage)

    print(f"\n{'team':<20}{'kills':>7}{'deaths':>8}   {'vs TA W/D/L':>12}{'TA kills':>10}{'faults':>8}")
    for team in sorted(teams, key=lambda t: -total(t, "teams", "kills")):
        wdl = "/".join(str(total(team, "ta", f)) for f in ("wins", "draws", "losses"))
        faults = total(team, "teams", "faults") + total(team, "ta", "faults")
        print(f"{team:<20}{total(team, 'teams', 'kills'):>7}{total(team, 'teams', 'deaths'):>8}   "
              f"{wdl:>12}{total(team, 'ta', 'kills'):>10}{faults:>8}")
    print(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()
