# BOMBcompeTItion

Development project, not research. A simplified Bomberland (CoderOne) game for an RL class assignment:
a 1v1 bomb game on one fixed 9x9 map, walls and bombs only, no items. Students should be able to read the
rules, write a bot and train it within about an hour on CPU. Remote: git@github.com:ahn-ml/BOMBcompeTItion.git.

## Where things are

- `bombcompetition/`: the package (`game.py` rules and `RULES`, `env.py` gym-style env, `match.py`, `render.py`, `view.py`).
- `submission/`: the student's bot (template, the folder they zip and hand in). `examples/`: `random`, `simple`.
  `ta_bots/`: TA reference bots (remove before the student release).
- `run_match.py`, `league.py`: matches and league with the submission limits. `tests/`: rule tests.
- `web/play.html`: play in the browser (built by `tools/build_web.py`).
- `README.md`: the student-facing rules and API. Keep it in sync with `RULES`.
- `ref-bomberland/`: upstream clone, read only, gitignored. `.kickoff/kickoff.txt`: the original brief.

## Current focus

Keep the base repo minimal and easy: a student should write a rule-based bot and submit it within an hour.
Left to teammates (do not start these here): RL training examples and checks, the evaluation environment
(Python / library versions, torch, uv or Docker), and TA bots.

## This project only

- Conversation in Korean, code, comments, files and commits in English.
- Commits: `<type>: summary`, author taegukang35 <chrsitianous@gmail.com>, no Claude co-author or session trailers.
- Approval before push, deleting, sending anything outside, or GPU jobs. Reading, coding and local tests: just do it.

@docs/agent/hub.md
