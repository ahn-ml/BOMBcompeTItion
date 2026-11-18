"""Rule tests. Run with `python -m pytest tests` or just `python tests/test_game.py`."""

import json
from pathlib import Path

import pytest
from gymnasium.utils.env_checker import check_env

from bombcompetition import N_CHANNELS, Action, BomberEnv, Game, Rules, parse
from bombcompetition.game import Bomb

A, B = 0, 1


def test_own_bomb_kills_but_is_not_a_kill():
    g = Game(Rules(lives=1))
    g.step(Action.BOMB, Action.STAY)
    assert g.bombs[(1, 1)].fuse == g.rules.fuse - 1
    g.step(Action.DOWN, Action.STAY)
    g.step(Action.UP, Action.STAY)  # cannot walk back onto the bomb
    assert g.pos[A] == (2, 1)
    for _ in range(g.rules.fuse - 3):
        g.step(Action.STAY, Action.STAY)
    assert g.done and g.lives == [0, 1] and g.winner() == B
    assert g.kills == [0, 0]


def test_kill_credit_when_both_die():
    g = Game(Rules(lives=1))
    g.pos = [(1, 3), (3, 1)]
    g.bombs = {(1, 1): Bomb(owner=A, fuse=1)}
    deaths = g.step(Action.STAY, Action.STAY)  # A's bomb at (1, 1) hits A at (1, 3) and B at (3, 1)
    assert g.lives == [0, 0] and g.kills == [1, 0]
    assert {(d.player, d.killer) for d in deaths} == {(A, None), (B, A)}


def test_same_target_cell_blocks_both():
    g = Game()
    g.pos = [(4, 1), (4, 3)]
    g.step(Action.RIGHT, Action.LEFT)
    assert g.pos == [(4, 1), (4, 3)]


def test_round_resets_after_death():
    g = Game(Rules(layout=("#####", "#...#", "#...#", "#...#", "#####"), starts=((1, 1), (3, 3)), fuse=2, radius=1))
    g.step(Action.BOMB, Action.STAY)
    g.step(Action.STAY, Action.STAY)
    assert g.lives == [2, 3] and not g.done
    assert g.pos == [(1, 1), (3, 3)] and not g.bombs


@pytest.mark.parametrize("rules", [
    Rules(layout=("#######", "#.....#", "#.#.#.#", "#.....#", "#######")),  # not square
    Rules(layout=("#####", "#A..#", "#....", "#..B#", "#####")),            # open border
    Rules(starts=((0, 0), (7, 7))),                                         # start on a wall
    Rules(starts=((1, 1), (1, 1))),                                         # same start
    Rules(fuse=0),
])
def test_bad_rules_are_rejected(rules):
    with pytest.raises(ValueError):
        Game(rules)


def test_observation():
    g = Game()
    g.step(Action.BOMB, Action.STAY)
    o0, o1 = g.obs(A), g.obs(B)
    assert o0.shape == (N_CHANNELS, 9, 9) and (o0[0] == o1[0]).all()
    v0, v1 = parse(o0), parse(o1)
    assert (v0.player, v0.me, v0.opp, v0.my_bombs) == (A, (1, 1), (7, 7), {(1, 1): 5})
    assert (v1.player, v1.me, v1.opp, v1.opp_bombs) == (B, (7, 7), (1, 1), {(1, 1): 5})
    assert (v1.my_lives, v1.steps_left) == (3, 299)


def test_env():
    for player in (A, B):
        env = BomberEnv(opponent=lambda obs: Action.STAY, player=player)
        check_env(env, skip_render_check=True)
        obs, _ = env.reset(seed=0)
        assert parse(obs).player == player


def test_matches_recorded_games():
    """40 random games recorded from the first implementation must replay identically."""
    traces = json.loads((Path(__file__).parent / "game_traces.json").read_text())
    for trace in traces:
        g = Game(Rules(layout=trace["layout"]))
        for (a0, a1), expected in zip(trace["acts"], trace["states"]):
            g.step(a0, a1)
            state = [*g.pos[0], *g.pos[1], *g.lives, *g.kills, len(g.bombs)]
            assert state == expected
        assert g.done


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
