import json
import random
from pathlib import Path

import pytest
from gymnasium.utils.env_checker import check_env

from bombcompetition import MAP, Action, BomberEnv, Game, Rules, legal_actions
from bombcompetition.game import TURN, Bomb

A, B = 0, 1
S = Action.STAY
PILLAR = ("#########", "#A......#", "#.#.#.#.#", "#.......#", "#.#.#.#.#", "#.......#", "#.#.#.#.#", "#......B#", "#########")


def test_own_bomb_kills_but_is_not_a_kill():
    g = Game(Rules(lives=1))
    g.step(Action.BOMB, S)
    g.step(Action.DOWN, S)
    g.step(Action.UP, S)  # cannot walk back onto the bomb
    assert g.pos[A] == (2, 1)
    for _ in range(g.rules.fuse - 3):
        g.step(S, S)
    assert g.done and g.lives == [0, 1] and g.kills == [0, 0] and g.winner() == B


def test_kill_credit_when_both_die():
    g = Game(Rules(lives=1))
    g.pos = [(1, 3), (3, 1)]
    g.bombs = {(1, 1): Bomb(owner=A, fuse=1)}  # reaches both players
    deaths = g.step(S, S)
    assert g.kills == [1, 0] and {(d.player, d.killer) for d in deaths} == {(A, None), (B, A)}


def test_same_target_cell_blocks_both():
    g = Game()
    g.pos = [(4, 1), (4, 3)]
    g.step(Action.RIGHT, Action.RIGHT)  # B moves RIGHT in its own view, LEFT on the board
    assert g.pos == [(4, 1), (4, 3)]


def test_round_resets_after_death():
    g = Game(Rules(layout=("#####", "#...#", "#...#", "#...#", "#####"), starts=((1, 1), (3, 3)), fuse=2, radius=1))
    g.step(Action.BOMB, S)
    g.step(S, S)
    assert g.lives == [2, 3] and g.pos == [(1, 1), (3, 3)] and not g.bombs and not g.done


@pytest.mark.parametrize("rules", [
    Rules(layout=("#######", "#.....#", "#######")),              # not square
    Rules(layout=("#####", "#A..#", "#....", "#..B#", "#####")),  # open border
    Rules(starts=((0, 0), (7, 7))),                               # start on a wall
    Rules(starts=((1, 1), (1, 1))),                               # same start
])
def test_bad_rules(rules):
    with pytest.raises(ValueError):
        Game(rules)


def test_observation():
    g = Game()
    for a0, a1 in [(Action.BOMB, Action.DOWN), (Action.DOWN, Action.BOMB), (Action.DOWN, Action.RIGHT)]:
        g.step(a0, a1)  # B's actions are in B's view: on the board B went UP, then LEFT
    assert g.pos == [(3, 1), (6, 7)]
    obs = g.obs(B)  # B's view is the board turned 180°
    assert (obs["player"], obs["me"], obs["opp"], obs["lives"], obs["step"]) == (B, (2, 1), (5, 7), (3, 3), 3)
    assert {(b["pos"], b["owner"], b["fuse"]) for b in obs["bombs"]} == {((7, 7), A, 2), ((2, 1), B, 3)}
    assert legal_actions(obs) == [Action.STAY, Action.BOMB, Action.UP, Action.DOWN]


def test_both_sides_see_the_same_game():
    """Swapping the bots gives the same game from each bot's side."""
    rng = random.Random(0)
    for _ in range(200):
        x, y = Game(), Game()
        while not x.done:
            a0, a1 = rng.randrange(6), rng.randrange(6)
            x.step(a0, a1)
            y.step(a1, a0)
            for p in (A, B):
                ox, oy = x.obs(p), y.obs(1 - p)
                assert (ox["me"], ox["opp"], ox["lives"]) == (oy["me"], oy["opp"], oy["lives"])
                assert (ox["walls"] == oy["walls"]).all()
                mine = lambda o: {(b["pos"], b["owner"] == o["player"], b["fuse"]) for b in o["bombs"]}
                assert mine(ox) == mine(oy)
            assert x.kills == y.kills[::-1] and x.done == y.done


def test_custom_reward():
    seen = []

    def reward_fn(prev_obs, action, obs, deaths):
        seen.append((prev_obs["step"], action, obs["step"]))
        return -0.5

    env = BomberEnv(opponent=lambda obs: S, reward_fn=reward_fn)
    env.reset()
    assert env.step(Action.UP)[1] == -0.5 and seen == [(0, Action.UP, 1)]


def test_env():
    for player in (A, B):
        check_env(BomberEnv(opponent=lambda obs: Action.BOMB, player=player), skip_render_check=True)


def test_recorded_games_replay_identically():
    traces = json.loads((Path(__file__).parent / "game_traces.json").read_text())
    for trace in traces:
        g = Game(Rules(layout={"rooms": MAP, "pillar": PILLAR}[trace["layout"]], fuse=6, max_bombs=2))  # recorded with the old rules
        for (a0, a1), expected in zip(trace["acts"], trace["states"]):
            g.step(a0, TURN[a1])  # recorded in board directions
            assert [*g.pos[0], *g.pos[1], *g.lives, *g.kills, len(g.bombs)] == expected
        assert g.done
