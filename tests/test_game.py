import copy
import json
from pathlib import Path

import pytest
from gymnasium.utils.env_checker import check_env

from bombcompetition import MAP, Action, BomberEnv, Game, Rules, parse, to_game
from bombcompetition.game import Bomb

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
    g.step(Action.RIGHT, Action.LEFT)
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


def test_observation_and_to_game():
    g = Game()
    for a0, a1 in [(Action.BOMB, Action.UP), (Action.DOWN, Action.BOMB), (Action.DOWN, Action.LEFT)]:
        g.step(a0, a1)
    v = parse(g.obs(B))
    assert (v.player, v.me, v.opp, v.my_lives, v.steps_left) == (B, (6, 7), (3, 1), 3, 297)
    assert v.my_bombs == {(6, 7): 4} and v.opp_bombs == {(1, 1): 3}
    for p in (A, B):
        rebuilt, real = to_game(g.obs(p)), copy.deepcopy(g)
        for _ in range(6):
            assert rebuilt.step(S, Action.LEFT) == real.step(S, Action.LEFT)
            assert (rebuilt.obs(p) == real.obs(p)).all()


def test_env():
    for player in (A, B):
        check_env(BomberEnv(opponent=lambda obs: S, player=player), skip_render_check=True)


def test_recorded_games_replay_identically():
    traces = json.loads((Path(__file__).parent / "game_traces.json").read_text())
    for trace in traces:
        g = Game(Rules(layout={"rooms": MAP, "pillar": PILLAR}[trace["layout"]]))
        for (a0, a1), expected in zip(trace["acts"], trace["states"]):
            g.step(a0, a1)
            assert [*g.pos[0], *g.pos[1], *g.lives, *g.kills, len(g.bombs)] == expected
        assert g.done
