---
name: orchestrator
description: "유튜브 콘텐츠 제작 에이전트 팀(트렌드 조사·대본·SEO·썸네일·검수)을 감독자가 조율하여 발행 가능한 콘텐츠 패키지를 만든다. 유튜브 영상 기획, 콘텐츠 제작, 영상 만들기, 채널 콘텐츠 준비, 다음 영상 뭐 찍지, 소재부터 대본·제목·썸네일까지 한번에, 쇼츠 기획 요청 시 반드시 이 스킬을 사용할 것. 후속 작업 — 이전 결과 수정, 부분 재실행, 대본만 다시, 제목만 다시 뽑기, 썸네일 컨셉 보완, 검수 다시, 업데이트, 개선, 다시 실행 요청 시에도 반드시 이 스킬을 사용할 것."
---

# YouTube Content Orchestrator

유튜브 콘텐츠 제작 팀을 조율하여 **조사 → 대본 → SEO/썸네일 → 검수 → 통합**까지 한 번에 수행한다.

## 실행 모드: 에이전트 팀

전 Phase에서 에이전트 팀 모드를 사용한다. 팀원 간 직접 통신이 품질의 핵심 동력이기 때문이다 — 대본의 결정적 순간이 썸네일 소재가 되고, 제목과 썸네일 카피는 서로를 보며 역할을 나눠야 하며, 조사 자료의 갭 발견이 즉시 대본 방향을 바꾼다. 이 교환을 감독자가 중계하면 병목이 되고 정보가 손실된다.

## 경로 규약

이 하네스는 플러그인으로 배포된다. **모든 산출물 경로는 하네스를 실행 중인 프로젝트의 루트 기준 상대 경로**이며, 플러그인이 어디에 설치되었는지와 무관하다. 작업 루트는 `youtube-content/`다.

| 용도 | 경로 |
|------|------|
| 중간 산출물 | `youtube-content/_workspace/` |
| 최종 산출물 | `youtube-content/outputs/{YYYYMMDD}-{slug}/content-package.md` |

에이전트 정의와 스킬은 플러그인이 제공하므로 **경로로 참조하지 않는다.** 에이전트는 `subagent_type`으로, 스킬은 Skill 툴의 스킬명으로 호출한다.

## 팀 구성

리더는 이 스킬을 실행하는 메인 세션이며, 감독자 역할을 수행한다. 시작 시 `youtube-content-harness:supervisor` 정의를 감독자 원칙으로 적용한다 — 메인 세션이 리더이므로 이 에이전트를 별도로 띄우지 않는다.

| 팀원 (`subagent_type`) | 사용 스킬 | 출력 |
|------|----------|------|
| `youtube-content-harness:trend-researcher` | `youtube-content-harness:trend-research` | `01_trend_research.md`, `01_angle_candidates.md` |
| `youtube-content-harness:script-writer` | `youtube-content-harness:script-writing` | `02_script.md` |
| `youtube-content-harness:seo-optimizer` | `youtube-content-harness:seo-optimization` | `03_seo.md` |
| `youtube-content-harness:thumbnail-planner` | `youtube-content-harness:thumbnail-concept` | `03_thumbnail.md` |
| `youtube-content-harness:content-reviewer` | `youtube-content-harness:content-review` | `04_review.md` |

**팀원 생성 방식:** 위 표의 `subagent_type`을 그대로 사용한다. 플러그인이 배포한 에이전트 정의가 자동 등록되므로, 정의 파일을 Read시키는 우회는 필요 없다 — 역할·원칙·통신 프로토콜이 시스템 프롬프트로 이미 주입된 상태로 기동한다. `model`은 전원 `opus`.

**프롬프트 필수 요소 (전 팀원 공통):** 에이전트 정의에는 역할만 있고 이번 실행의 경로는 없다. 팀원은 프로젝트 루트에서 실행되므로 다음 2가지가 빠지면 파일을 엉뚱한 위치에 쓴다.
1. **입력 파일의 `youtube-content/_workspace/...` 전체 경로**
2. **출력 파일의 `youtube-content/_workspace/...` 전체 경로**

## 워크플로우

### Phase 0: 컨텍스트 확인

`youtube-content/_workspace/` 존재 여부로 실행 모드를 정한다.

| 상태 | 모드 | 행동 |
|------|------|------|
| 미존재 | **초기 실행** | Phase 1로 진행 |
| 존재 + 사용자가 부분 수정 요청 | **부분 재실행** | Phase 1 건너뛰고 아래 "부분 재실행" 절차 |
| 존재 + 새 주제/새 입력 | **새 실행** | `youtube-content/_workspace/`를 `youtube-content/_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1 |

애매하면 사용자에게 묻는다. 기존 산출물을 덮어쓰는 것은 되돌리기 어렵기 때문이다.

**부분 재실행 절차:**
1. 어떤 산출물이 대상인지 특정한다 (예: "제목이 밋밋하다" → `03_seo.md`, seo-optimizer)
2. 해당 팀원만 포함해 팀을 구성한다. 필요하면 content-reviewer를 함께 소집한다
3. 팀원 프롬프트에 **이전 산출물 경로 + 사용자 피드백 원문**을 그대로 포함한다. 요약하지 않는다 — 요약 과정에서 사용자가 지적한 뉘앙스가 사라진다
4. 수정 완료 후 content-reviewer로 **영향받는 경계면만** 재검증한다 (제목 변경 → 경계면 1·3, 대본 변경 → 1·2·4)
5. Phase 5로 진행해 최종 패키지를 갱신한다

### Phase 1: 준비

1. 사용자 입력에서 다음을 파악한다. 없으면 묻는다:
   - **주제 영역** (필수)
   - **채널 컨셉 / 타깃 시청자** (없으면 조사 후 제안)
   - **포맷**: 롱폼 / 숏폼 / 롱폼+숏폼 파생 (없으면 조사 결과의 추천 포맷을 따름)
2. `youtube-content/_workspace/` 생성
3. 입력을 `youtube-content/_workspace/00_input.md`에 기록 (사용자 요청 원문 포함)

### Phase 2: 조사 및 앵글 확정

**실행 방식:** trend-researcher 단독 → 감독자 결정 → 사용자 확인

이 Phase만 팀을 부분 구성한다. 앵글이 확정되기 전에 나머지 4명을 띄우면 유휴 대기하며 토큰만 소비하고, 앵글이 바뀌면 전량 재작업이 되기 때문이다.

1. 팀 생성 (1인):
   ```
   TeamCreate(
     team_name: "youtube-content-team",
     members: [
       { name: "trend-researcher",
         agent_type: "youtube-content-harness:trend-researcher", model: "opus",
         prompt: "주제: {주제}. 타깃: {타깃}.
                  산출물: youtube-content/_workspace/01_trend_research.md,
                          youtube-content/_workspace/01_angle_candidates.md" }
     ]
   )
   ```
2. TaskCreate로 조사 4축 + 앵글 도출 작업 등록
3. `01_angle_candidates.md` 완성 후 감독자가 앵글 1개를 선정한다. 선정 기준:
   - 포화도가 낮거나 중간이고, 검증 문장이 완결된 것
   - 리스크가 명시되어 있고 감수 가능한 것
   - 채널 컨셉과 타깃이 일치하는 것
4. **사용자에게 확정 앵글을 제시하고 승인받는다.** 이 하네스에서 사용자 확인은 여기 한 번뿐이다. 대본이 나온 뒤 앵글을 바꾸면 전량 재작업이기 때문이다
5. 선택되지 않은 앵글은 `youtube-content/_workspace/01_angle_backlog.md`로 보존한다

### Phase 3: 대본 작성

**실행 방식:** 에이전트 팀 (trend-researcher 유지 + script-writer 합류)

1. `TeamCreate`가 이미 활성이므로 팀원을 추가 소집한다. 불가하면 `TeamDelete` 후 두 명으로 재구성한다
2. 전체 브리핑 (`SendMessage to: "all"`): 확정 앵글, 타깃, 포맷, 조사 파일 경로
3. TaskCreate:
   - `대본 작성` (script-writer) — `depends_on`: 조사 완료
   - `사실 근거 지원` (trend-researcher) — script-writer의 요청에 응답 대기
4. **통신 규칙:** script-writer가 조사 자료에 없는 사실이 필요하면 trend-researcher에게 SendMessage로 직접 요청한다. 감독자를 경유하지 않는다
5. 완료 조건: `02_script.md`에 `## 썸네일/제목 소재`와 `## 다루지 않은 주제`가 채워져 있을 것. 비어 있으면 감독자가 반려한다 — 이 두 섹션이 Phase 4의 유일한 입력이기 때문이다

### Phase 4: SEO + 썸네일 (병렬)

**실행 방식:** 에이전트 팀 (seo-optimizer + thumbnail-planner 동시)

1. 두 팀원을 소집하고 대본 완성을 알린다
2. TaskCreate:
   - `SEO 메타데이터 작성` (seo-optimizer)
   - `썸네일 컨셉 기획` (thumbnail-planner)
   - `제목-카피 역할 분담 합의` (양쪽 공동)
3. **통신 규칙 — 이 Phase의 핵심:**
   - seo-optimizer는 추천 제목안이 정해지는 즉시 thumbnail-planner에게 SendMessage로 전달한다. 동시에 **"제목이 말하지 않은 것"**을 함께 보낸다
   - thumbnail-planner는 카피 초안과 그것이 담당하는 정보 축을 seo-optimizer에게 회신한다
   - 중복이 발견되면 두 사람이 직접 역할을 재분담한다. **합의 실패 시에만** 감독자가 개입해 어느 쪽이 양보할지 결정한다
   - 둘 중 하나라도 대본에 없는 소재를 쓰고 싶으면 script-writer에게 직접 문의한다
4. 감독자는 두 산출물이 완료될 때까지 개입하지 않는다. 조기 개입은 병렬성을 죽인다

### Phase 5: 검수 및 재작업 루프

**실행 방식:** 에이전트 팀 (content-reviewer 합류)

1. content-reviewer 소집, `youtube-content/_workspace/` 전체를 입력으로 지정
2. 검수 완료 → `04_review.md`의 판정 확인
3. **PASS** → Phase 6
4. **REVISE** → 재작업 루프:
   - 감독자가 치명적 결함을 담당 팀원별로 묶는다
   - 각 팀원에게 SendMessage로 결함 근거를 **그대로** 전달한다. 어떻게 고칠지는 팀원이 판단하게 둔다 — 감독자가 해법까지 지정하면 전문성이 무의미해진다
   - 수정 완료 후 재검수 (영향받는 경계면만)
   - **최대 2회.** 3회차 진입 시 남은 결함을 최종 패키지의 `## 알려진 한계`에 기록하고 Phase 6으로 넘어간다. 개선의 한계효용보다 무한 루프의 비용이 크기 때문이다

### Phase 6: 통합 및 정리

1. `youtube-content/_workspace/` 산출물을 하나의 발행 가능한 문서로 통합:
   `youtube-content/outputs/{YYYYMMDD}-{slug}/content-package.md`
2. 통합 시 감독자가 직접 확인할 것:
   - trend-researcher의 수치에 출처가 붙어 있는가. 없으면 "추정"으로 표기하거나 제거한다
   - 조사 모드가 폴백이었다면 패키지 상단에 명시한다
3. 팀원에게 종료 알림 → `TeamDelete`
4. `youtube-content/_workspace/`는 **삭제하지 않는다** (사후 검증·부분 재실행의 입력)
5. 사용자에게 요약 보고: 확정 앵글, 추천 제목, 추천 썸네일 컨셉, 검수 판정, 알려진 한계
6. 피드백 요청: "결과에서 개선할 부분이나 팀 구성에서 바꾸고 싶은 점이 있나요?"

## 최종 산출물 구조

`content-package.md`:

```markdown
# {영상 제목(추천안)}

> 포맷: {} | 타깃: {} | 검수: {PASS|한계 있음} | 조사 모드: {}

## 1. 앵글
{검증 문장} / 리스크: {}

## 2. 대본
{02_script.md 본문}

## 3. 제목·설명·태그
{03_seo.md 핵심 — 추천 제목 + 대안 4안, 설명란 전문, 챕터, 태그, 해시태그}

## 4. 썸네일 컨셉
{03_thumbnail.md — 컨셉별 제작 지시서 + 이미지 생성 프롬프트 + A/B 계획}

## 5. 근거 자료
{조사 자료 중 대본이 인용한 사실과 출처}

## 6. 검수 결과
{교차 검증 매트릭스 요약}

## 7. 알려진 한계
{미해소 결함, 폴백 모드 여부, 검증 불가 항목}
```

## 데이터 흐름

```
사용자 입력
    ↓
[감독자] ──→ trend-researcher ──→ 01_trend_research.md
                                  01_angle_candidates.md
    ↓ 앵글 선정 + 사용자 승인
[감독자] ──브리핑(all)──→ script-writer ←SendMessage→ trend-researcher
                              ↓ 02_script.md
              ┌───────────────┴───────────────┐
              ↓                               ↓
        seo-optimizer  ←──SendMessage──→  thumbnail-planner
        03_seo.md          (카피 분담)      03_thumbnail.md
              └───────────────┬───────────────┘
                              ↓
                      content-reviewer → 04_review.md
                              ↓ REVISE(최대 2회) ↺
                         [감독자: 통합]
                              ↓
              outputs/{date}-{slug}/content-package.md
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| trend-researcher 웹 검색 불가 | 폴백 모드 선언 → 사용자에게 키워드·자료 요청 → 미제공 시 도메인 지식으로 앵글 제안 후 승인. 이후 전 산출물에서 수치 제거 |
| 앵글 후보가 3개 미만 | 부족한 채로 제시하고 주제 범위 확대를 사용자에게 제안 |
| script-writer가 근거 부족으로 막힘 | `[근거 필요: ]` 플레이스홀더 허용, 검수에서 치명적 결함 처리. 감독자가 조사 보강 여부 결정 |
| seo/thumbnail 카피 중복 합의 실패 | 감독자가 결정. 원칙 — 제목이 "무엇을", 썸네일이 "왜/얼마나" |
| 팀원 1명 실패 | SendMessage로 상태 확인 → 1회 재시작 → 재실패 시 해당 영역을 패키지에 "미완성"으로 명시하고 진행 |
| content-reviewer 실패 | 감독자가 `youtube-content-harness:content-review` 스킬의 경계면 5종을 직접 수행 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| REVISE 3회차 | 루프 종료. 남은 결함을 `## 알려진 한계`에 기록 |
| 산출물 간 상충 데이터 | 삭제하지 않고 출처 병기 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "개발팀 리드 대상 채널인데, AI 코딩 도구 관련 롱폼 하나 기획해줘"
2. Phase 1 — 주제/타깃/포맷 확정, `youtube-content/_workspace/` 생성
3. Phase 2 — trend-researcher가 앵글 후보 4개 도출, 감독자가 2번 선정, 사용자 승인
4. Phase 3 — script-writer가 10분 롱폼 대본 작성 (훅 3안, 약속-이행 매핑, 썸네일 소재 5개)
5. Phase 4 — seo-optimizer 제목 5안 + thumbnail-planner 컨셉 3안, SendMessage로 카피 중복 해소
6. Phase 5 — content-reviewer PASS
7. Phase 6 — `outputs/20260723-ai-tool-team-review/content-package.md` 생성
8. 예상: 경계면 5종 전부 근거 위치와 함께 통과 기록

### 에러 흐름 A — 검색 불가
1. Phase 2에서 웹 검색이 3회 무의미한 결과 반환
2. trend-researcher가 폴백 모드 선언, 산출물에 명시
3. 감독자가 사용자에게 참고 자료 요청 → 미제공
4. 도메인 지식으로 앵글 3개 제안 → 사용자 승인
5. 대본에 수치 없이 정성적 서술만 사용
6. content-reviewer가 사실 근거 추적을 건너뛰되 수치 등장 여부만 확인
7. 최종 패키지 상단에 `조사 모드: 폴백` 명시

### 에러 흐름 B — REVISE 한도 초과
1. Phase 5 1회차: 치명적 결함 3건 (제목 약속 불이행 1, 썸네일 장면 부재 1, 출처 없는 수치 1)
2. 감독자가 seo-optimizer·thumbnail-planner·script-writer에게 각각 전달, 수정
3. 2회차: 결함 2건 해소, 1건 잔존 + 제목 변경으로 카피 중복 신규 발생 1건
4. 3회차 진입 금지 → 잔존 2건을 `## 알려진 한계`에 기록
5. Phase 6 진행, 사용자 보고 시 미해소 항목을 명시
