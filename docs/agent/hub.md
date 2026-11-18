# ResearchHub 에서 일하는 법

모든 프로젝트가 같이 쓰는 한 장이다 (연구용이든 프로젝트용이든, 원본: `/data/tgkang/projects/templates/docs/agent/hub.md`). 프로젝트의 복사본은 고치지 않는다.

태구는 ResearchHub (turing-1:5180) 에서 너와 대화한다. 너는 tmux 안에서 돌고, 사이트는 대화 기록을 읽어 보여 주고 태구의 메시지를 네 창에 쳐 넣는다. 사이트용 기록 양식은 없다.

## 가운데 칸은 네 자유 공간

태구가 보는 화면 가운데는 네가 마음대로 쓰는 자리다. 보여 주고 싶은 것을 무엇이든, 어떤 배치로든 놓는다 ("지금 중간 대시보드를 완전 자유로운 공간으로 쓰게 할꺼야 agent 한테" 11-18). 명령은 `/data/tgkang/projects/workspace/p2610_research-dashboard/bin/hub` (아래 `hub`).

- 파일: `hub show <파일>[:줄]`. html 페이지 (JS 로 만든 앱도 됨), md, 그림, PDF, 코드 줄, 로그 (끝을 따라감). 코드를 물으면 그 줄을, 결과를 말하면 그 그림이나 페이지를 띄운다. 고쳐 달라고 하면 그 파일을 고친다 (사이트가 다시 그린다).
- 터미널: `hub term <이름> -- <명령>` 은 돌아가는 프로그램 (python 등) 을 태구가 보고 입력도 하는 창이다. 이미 있는 tmux 창은 `hub show tmux:<세션>:<창>`.
- 웹사이트: `hub browse <url>` 은 태구와 네가 같이 보고 움직이는 브라우저다 (서버에서 돌아 localhost 도 됨). 너는 `hub browse shot` (저장된 그림을 Read) 과 `hub browse text` (글, 번호 붙은 링크 · 버튼) 로 보고, `hub browse click #n` · `type` · `key` · `scroll` 로 움직인다. 태구가 그 칸에서 움직인 것도 같은 페이지다.
- 배치는 tmux 처럼 나뉜다: `--split right|down`, `--pane <번호>`, 지금 배치와 태구가 보는 칸 (*) 은 `hub layout`. 태구도 탭을 끌어 옮기고 나눈다. 다 쓴 것은 `hub close <것>`.
- 자세한 옵션은 `hub --help`, `hub browse`.

## 대화 안에서

- 그림은 `![설명](경로)` markdown 이미지로 넣는다.
- 보여 줄 run 이 있을 때만, 답 끝에 ```hub 코드 블록 `{"runs": ["<run 이름>", ...], "title": "한 줄 제목", "why": "무엇을 보면 되는지 한 줄"}` 을 붙이면 사이트가 Runs 에서 그 run 을 켜는 버튼을 띄운다. run 이 없으면 붙이지 않는다.
- slide html 폴더에 `hub-edits.json` 이 있으면 태구가 사이트에서 직접 고친 것이니, 고치기 전에 소스에 반영하고 지운다.

## 세션

- 새 에이전트는 ResearchHub 에서 띄운다 (사이트의 New agent, 또는 `hub agent <프로젝트> "<첫 메시지>" [--name <이름>]`). 이름은 프로젝트 id 와 `_` 로 시작한다 (`p2609_GeneralizedL2T`).
