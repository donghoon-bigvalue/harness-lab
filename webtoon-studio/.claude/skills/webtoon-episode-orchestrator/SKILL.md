---
name: webtoon-episode-orchestrator
description: "웹툰 에피소드 제작 에이전트 팀(스토리·캐릭터·패널·대사·스타일 가디언)을 조율하여 회차 원고 패키지와 콘티를 산출하는 오케스트레이터. 웹툰 회차를 만들어달라·에피소드를 제작해달라·N화를 써달라는 요청, 웹툰 기획/연출/콘티/캐릭터/대사 작업 전반, 그리고 후속 작업 — 다시 실행, 재실행, 업데이트, 수정, 보완, 이전 결과 개선, '대사만 다시', '컷을 다시 나눠줘', '캐릭터만 새로', '콘티 다시 뽑아줘', '리뷰 한 번 더' — 요청 시에도 반드시 이 스킬을 사용할 것. webtoon-studio 하네스의 진입점이며, 개별 스킬을 직접 호출하기 전에 이 스킬로 실행 모드(초기/부분 재실행/새 회차)를 먼저 판별한다."
---

# 웹툰 에피소드 오케스트레이터

`webtoon-studio` 하네스의 진입점. 5개 에이전트를 조율해 한 회차의 원고 패키지와 콘티를 만든다.

## 실행 모드: 하이브리드

이 세션에는 `TeamCreate`/`TaskCreate`가 없으므로, 팀 통신은 **명명된 백그라운드 서브에이전트 + `SendMessage`** 로 구현한다. 제작 에이전트를 살려두고 개정 지시를 `SendMessage`로 보내면, 재스폰 대비 자기 산출물의 맥락이 보존되어 개정 품질이 높다. 산출물 자체는 전부 파일로 오간다 — 파일이어야 교차 리뷰에서 다섯 명이 같은 것을 보고, 사후에 왜 그렇게 고쳤는지 추적된다.

| Phase | 모드 | 이유 |
|-------|------|------|
| 2 바이블 | 단일 서브에이전트 | 정본은 한 명만 쓴다. 동시 편집하면 정본이 사라진다 |
| 3 제작 | 서브에이전트 팬아웃 (명명·백그라운드) | 의존 없는 구간은 병렬. 이름을 붙여 SendMessage 채널을 확보한다 |
| 4 교차 리뷰 | 서브에이전트 팬아웃 (5인) | 서로의 지적에 영향받지 않아야 관점이 독립적으로 남는다 |
| 5 중재·개정 | SendMessage 피드백 루프 | 제작 맥락을 가진 원 에이전트가 고치는 편이 정확하다 |
| 6 조립 | 리더 직접 | 스크립트 실행과 파일 병합뿐이라 위임 이득이 없다 |

> `TeamCreate`가 사용 가능한 환경이면 Phase 3~5를 팀 모드로 대체할 수 있다. 그 경우 Phase 4의 독립성을 유지하기 위해, 리뷰 작성 완료 전에는 팀원 간 리뷰 내용 공유를 금지한다.

## 에이전트 구성

| 에이전트 | subagent_type | 스킬 | 산출물 |
|---------|---------------|------|--------|
| style-guardian | `general-purpose` | webtoon-style-consistency | `01_style_bible.md`, `07_consistency_report.md` |
| story-writer | `general-purpose` | webtoon-story-writing | `02_story_beatsheet.md` |
| character-designer | `general-purpose` | webtoon-character-prompting | `03_character_sheet.json`, `03_character_prompts.md` |
| panel-planner | `general-purpose` | webtoon-panel-layout | `04_panel_layout.json`, `09_conti.html` |
| dialogue-editor | `general-purpose` | webtoon-dialogue-editing | `05_dialogue_script.json` |

**모든 Agent 호출에 `model: "opus"`를 명시한다.**

에이전트 정의는 `webtoon-studio/.claude/agents/{이름}.md`에 있다. 서브에이전트 타입 해석에 의존하지 않도록, 프롬프트 첫 줄에서 **자기 정의 파일을 Read하라고 지시**한다. 이렇게 하면 커스텀 타입이 등록되지 않은 환경에서도 역할·프로토콜이 동일하게 전달된다.

모든 에이전트 프롬프트에 공통으로 넣을 것:

```
1. webtoon-studio/.claude/agents/{당신}.md 를 Read하여 역할 정의를 로드하라.
2. webtoon-studio/.claude/skills/{당신의 스킬}/SKILL.md 를 Read하여 작업 절차를 로드하라.
3. 작업 디렉토리: {WORKDIR}
4. 산출물 경로: {WORKDIR}/_workspace/{파일명}
5. 완료 시 반환 메시지는 3줄 이내 요약 + 산출물 경로만. 본문을 반환에 담지 마라.
```

## 워크플로우

### Phase 0: 컨텍스트 확인

`webtoon-studio/episodes/` 와 활성 `_workspace/`를 확인해 실행 모드를 결정한다.

| 상황 | 모드 | 행동 |
|------|------|------|
| `_workspace/` 없음 | **초기 실행** | Phase 1로 |
| `_workspace/` 있음 + 부분 수정 요청 ("대사만", "컷 다시") | **부분 재실행** | 해당 Phase만. 앞 산출물은 재사용하고 덮어쓰지 않는다 |
| `_workspace/` 있음 + 새 회차 입력 | **새 실행** | `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1 |
| `_workspace/` 있음 + 리뷰만 재요청 | **리뷰 재실행** | Phase 4~5만, 라운드 번호 +1 |

부분 재실행 시 대상 판정:

| 사용자 표현 | 재실행 대상 | 연쇄 |
|------------|-----------|------|
| 스토리·전개·훅 | story-writer | 패널·대사도 영향 → 사용자에게 연쇄 범위 확인 |
| 캐릭터·외형·프롬프트 | character-designer | 없음 (앵커 변경이면 바이블 개정 선행) |
| 컷·연출·콘티·리듬 | panel-planner | 슬롯이 바뀌면 dialogue-editor 연쇄 |
| 대사·말투·분량 | dialogue-editor | 없음 |
| 톤·스타일·일관성 | style-guardian | 바이블 개정 시 전원 연쇄 |

**연쇄가 있으면 사용자에게 먼저 알린다.** 스토리만 고치고 패널을 두면 `beat` 참조가 깨진 패키지가 나오는데, 이는 조용히 진행하면 조립 단계에서야 드러난다.

### Phase 1: 준비

1. 사용자 입력에서 확보한다: 작품명, 회차 번호, 장르·톤, 로그라인 또는 이번 화 소재, 등장 인물, 컷 예산, 참고 레퍼런스
2. 누락 항목은 **바이블 기본값으로 채우되 채웠다는 사실을 기록**한다. 필수 누락(작품명·이번 화 소재)만 사용자에게 묻는다 — 나머지까지 물으면 진행이 막힌다
3. `{WORKDIR}/_workspace/` 생성. `{WORKDIR}`은 `webtoon-studio`
4. 입력을 `_workspace/00_input.md`에 저장

### Phase 2: 스타일 바이블 확정

**style-guardian 단독.** 네 명이 병렬로 만들기 전에 공통 기준이 있어야 일관성이 성립한다. 이 순서를 뒤집으면 서로 다른 전제 위에 쌓인 산출물이 나와 수정이 연쇄한다.

```
Agent(
  name: "style-guardian",
  subagent_type: "general-purpose",
  model: "opus",
  run_in_background: false,
  prompt: "<공통 프롬프트> + 00_input.md와 (있다면) webtoon-studio/series-bible.md를 읽고
           _workspace/01_style_bible.md를 작성하라. 모든 규칙에 SB-* ID와 검증 방법을 붙이고,
           추정으로 채운 항목은 8절 미해결 쟁점에 남겨라."
)
```

동기 실행이다. 바이블 없이 다음 Phase를 시작할 수 없다.

바이블 산출 후 **8절 미해결 쟁점을 사용자에게 보고**한다. 여기서 사용자가 뒤집으면 비용이 가장 싸다.

### Phase 3: 제작 (팬아웃)

의존 관계에 따라 3단계로 나눈다. 각 에이전트는 `name`을 붙이고 `run_in_background: true`로 띄워 Phase 5의 SendMessage 채널을 확보한다.

**3a. 스토리** — 나머지 셋의 공통 입력이므로 단독 선행.

```
Agent(name: "story-writer", subagent_type: "general-purpose", model: "opus",
      run_in_background: true,
      prompt: "<공통> + 01_style_bible.md, 00_input.md를 읽고 _workspace/02_story_beatsheet.md 작성")
```

**3b. 캐릭터 ∥ 패널** — 둘 다 비트시트에만 의존하므로 병렬. 한 메시지에서 동시에 호출한다.

```
Agent(name: "character-designer", ..., run_in_background: true,
      prompt: "<공통> + 01, 02를 읽고 _workspace/03_character_sheet.json + 03_character_prompts.md 작성")
Agent(name: "panel-planner", ..., run_in_background: true,
      prompt: "<공통> + 01, 02를 읽고 _workspace/04_panel_layout.json 작성.
               말풍선은 슬롯만 선언하고 텍스트는 쓰지 마라.
               작성 후 render_conti.py로 _workspace/09_conti.html을 렌더해 리듬을 자가 검수하라.")
```

**3c. 대사** — 패널의 슬롯이 있어야 채울 수 있으므로 3b 완료 후.

```
Agent(name: "dialogue-editor", ..., run_in_background: true,
      prompt: "<공통> + 01,02,03,04를 읽고 _workspace/05_dialogue_script.json 작성.
               작성 후 validate_package.py를 돌려 BLOCKER 0을 확인한 뒤 완료 보고하라.")
```

### Phase 4: 교차 리뷰

**리뷰 전에 리더가 정합성 검증을 먼저 돌린다:**

```bash
python3 webtoon-studio/.claude/skills/webtoon-style-consistency/scripts/validate_package.py \
  --panels {WORKDIR}/_workspace/04_panel_layout.json \
  --dialogue {WORKDIR}/_workspace/05_dialogue_script.json \
  --characters {WORKDIR}/_workspace/03_character_sheet.json
```

종료 코드 2(BLOCKER)면 리뷰를 시작하지 않는다. 참조가 깨진 상태로 리뷰하면 다섯 명의 지적이 전부 그 한 원인으로 수렴해 나머지 관점이 묻힌다. 해당 에이전트에게 SendMessage로 수정을 요청하고 재검증한다.

검증 통과 후 5개 리뷰를 **한 메시지에서 동시 호출**한다. 리뷰어는 자기 산출물을 리뷰하지 않는다.

| 리뷰어 | 대상 | 렌즈 | 출력 |
|--------|------|------|------|
| story-writer | 04, 05 | 서사 의도 보존 | `06_review_story-writer.md` |
| character-designer | 02, 04 | 캐릭터 앵커 일관성 | `06_review_character-designer.md` |
| panel-planner | 02, 05 | 스크롤 수용력 | `06_review_panel-planner.md` |
| dialogue-editor | 02, 04 | 화법·분량 | `06_review_dialogue-editor.md` |
| style-guardian | 02~05 | 바이블 준수 전반 | `06_review_style-guardian.md` |

이미 살아 있는 에이전트에는 `SendMessage`로 리뷰를 요청한다 — 자기 산출물의 근거를 기억한 상태에서 남의 것을 보면 지적이 구체적이다.

**리뷰 중에는 리뷰어 간 교신을 금지한다.** 먼저 나온 지적이 다른 리뷰어의 관점을 덮으면 교차 리뷰의 이점이 사라진다.

### Phase 5: 중재 및 개정

1. style-guardian에게 5개 리뷰 종합을 요청 → `_workspace/07_consistency_report.md`
2. 리포트의 판정에 따라 분기:
   - `PASS` → Phase 6
   - `REVISE` → 개정 라운드 진행
   - `BLOCKED` → 사용자에게 보고하고 결정을 받는다
3. 개정 라운드: 각 제작 에이전트에게 **자기 앞 개정 지시만** SendMessage로 전달. 수정본은 `_workspace/08_r{N}_{artifact}`에 저장하고 원본은 남긴다
4. 개정 후 style-guardian이 **개정본만** 재검수. 전체 재리뷰는 하지 않는다
5. **최대 2라운드.** 3라운드째부터는 개선폭이 비용을 밑돌고 루프 위험이 실질적이다. 잔여 MAJOR는 리포트에 "미해결"로 명시하고 진행한다

"사용자 결정 필요" 항목이 있으면 여기서 사용자에게 묻는다.

### Phase 6: 조립

1. 개정본이 있으면 `08_r{N}_*`를 정본으로 삼아 콘티를 다시 렌더한다:
   ```bash
   python3 webtoon-studio/.claude/skills/webtoon-panel-layout/scripts/render_conti.py \
     --panels {최신 panel_layout} --dialogue {최신 dialogue_script} \
     --out {WORKDIR}/_workspace/09_conti.html
   ```
2. 정합성 검증을 최종 1회 더 돌린다 (개정이 새 깨짐을 만들었을 수 있다)
3. `webtoon-studio/episodes/{회차번호 3자리}-{슬러그}/`에 패키지를 조립한다:

   | 파일 | 내용 |
   |------|------|
   | `episode.md` | 통합 원고 — 회차 요약, 비트별로 컷·대사를 배열한 제작용 본문 |
   | `story_beatsheet.md` | 비트시트 |
   | `character_sheet.json` / `character_prompts.md` | 캐릭터 명세와 생성 프롬프트 |
   | `panel_layout.json` | 패널 레이아웃 |
   | `dialogue_script.json` | 대사 스크립트 |
   | `conti.html` | 콘티 목업 |
   | `style_bible.md` | 이 회차 적용 바이블 스냅샷 |
   | `consistency_report.md` | 일관성 리포트 (미해결 항목 포함) |

4. `webtoon-studio/series-bible.md`에 신규 규칙과 확정된 결정 사항을 병합한다. 이 병합을 건너뛰면 다음 회차가 같은 논쟁을 반복한다

### Phase 7: 정리 및 피드백

1. 살아 있는 에이전트를 종료한다 (`TaskStop`)
2. `_workspace/`는 **삭제하지 않는다** — 사후 검증과 감사 추적에 쓴다
3. 사용자에게 보고: 산출 경로, 컷/말풍선 수, 리뷰 라운드 수, 채택/기각 건수, **미해결 항목**
4. 피드백을 요청한다: 결과에서 고칠 부분, 팀 구성이나 순서에서 바꾸고 싶은 점. 답이 없으면 넘어간다

피드백이 오면 반영 대상이 다르다:

| 피드백 | 수정 대상 |
|--------|----------|
| 산출물 품질 | 해당 에이전트의 스킬 |
| 역할 범위 | 에이전트 정의 `.md` |
| 순서·라운드 수 | 이 오케스트레이터 |
| 트리거 안 됨 | 스킬 description |

변경은 루트 `CLAUDE.md`의 변경 이력에 기록한다.

## 데이터 흐름

```
00_input ─→ [style-guardian] ─→ 01_style_bible
                                     │
                                     ├─→ [story-writer] ─→ 02_beatsheet
                                     │                          │
                    ┌────────────────┴──────────────────────────┤
                    ↓                                           ↓
        [character-designer] → 03_character_*        [panel-planner] → 04_panel_layout
                    │                                           │
                    │                                           ↓
                    │                              [dialogue-editor] → 05_dialogue_script
                    │                                           │
                    └───────────→ validate_package.py ←─────────┘
                                     │ (BLOCKER 0)
                                     ↓
                    5인 교차 리뷰 → 06_review_* (독립 작성)
                                     ↓
                    [style-guardian 중재] → 07_consistency_report
                                     ↓  SendMessage 개정 지시 (최대 2라운드)
                              08_r{N}_* 개정본
                                     ↓
                    render_conti.py → 09_conti.html
                                     ↓
                          episodes/{NNN}-{slug}/
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 에이전트 1명 실패 | 1회 재시도. 재실패 시 리더가 해당 산출물을 최소 형태로 채우고 리포트에 "자동 생성 — 검수 필요" 명시 |
| style-guardian 실패 | 진행 중단. 바이블 없이 만든 산출물은 일관성 검수 기준이 없어 뒤에서 전부 재작업이 된다 |
| `validate_package.py` BLOCKER 2회 연속 | 리뷰를 건너뛰고 사용자에게 보고. 자동 복구를 반복하면 에이전트가 참조를 임의로 지워 맞추기 시작한다 |
| 리뷰 지적 상충 | 삭제하지 않고 병기. 상위 규칙(`SB-NEVER > SB-CHAR > SB-TONE/ART > 나머지`)으로 판정, 동급이면 사용자 결정 |
| 개정 2라운드 후에도 MAJOR 잔존 | "미해결"로 명시하고 조립 진행. 감춘 미해결이 조용히 조립되는 것보다 낫다 |
| 컷 예산 초과 | panel-planner가 임의 삭제하지 않고 story-writer에게 비트 축소를 요청 |
| 콘티 렌더 실패 | 패키지 조립은 계속하되 `conti.html` 누락을 보고. 원고 자체는 유효하다 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "새벽의 관측자 3화 만들어줘. 옥상에서 세 번째 신호를 받는 이야기, 60컷 정도"
2. Phase 0 → `_workspace/` 없음 → 초기 실행
3. Phase 2 → 바이블 확정, 미해결 쟁점 2건 사용자 보고
4. Phase 3 → 비트시트 → (캐릭터 ∥ 패널) → 대사
5. Phase 4 → 정합성 검증 통과 → 5인 리뷰
6. Phase 5 → 리포트 `REVISE`, 1라운드 개정 후 `PASS`
7. Phase 6 → `episodes/003-지붕-위의-신호/` 생성
8. 예상 결과: 8개 파일 패키지 + 콘티 HTML

### 에러 흐름
1. Phase 3c에서 dialogue-editor가 존재하지 않는 슬롯 `P07-B3`을 참조
2. Phase 4 진입 시 `validate_package.py`가 종료 코드 2 반환
3. 리더가 리뷰를 시작하지 않고 dialogue-editor에게 SendMessage로 수정 요청
4. 재검증 통과 → 리뷰 정상 진행
5. 2회 연속 실패였다면 사용자에게 보고하고 중단

### 부분 재실행 흐름
1. 사용자: "대사가 너무 설명적이야. 대사만 다시"
2. Phase 0 → 부분 재실행, 대상 dialogue-editor, 연쇄 없음
3. `08_r{N}_dialogue_script.json` 생성 → 정합성 검증 → style-guardian 재검수
4. Phase 6에서 콘티 재렌더 + 패키지 갱신
